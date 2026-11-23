# [AI 사용 주석]
# - AI 종류: Claude (Anthropic, Claude Opus 5.5)
# - 사용 목적: 요구서의 모듈2 기능(등록·중복 체크, 조회·검색, 수정·BMI 재계산, 삭제·파일 동기,
#   통계)을 모듈1(HealthDB)과 연결되도록 작성한 health_logic.py 전체 코드 생성
#   → 실행 코드와 주석 모두 AI가 작성함
# - 사용 프롬프트:
#   (1) "모듈2 health_logic.py (비즈니스로직) 핵심비즈니스규칙및 CRUD • 신규등록및중복체크: ..."
#        요구서의 예외처리·UX·코드 품질·제약사항 요구사항 전문 붙여넣음
# - 본인 수정: (직접 고친 부분이 있으면 적기)
# - 사용한 사람: 조하늘 (202611844)
# - 날짜: 2026-11-24
"""health_logic.py - 모듈2: 비즈니스 로직 (핵심 규칙 및 CRUD)

파일 위치와 입출력은 모듈1(health_db.py)의 HealthDB가 담당한다 (data/ 폴더).
    load_json()            -> 저장된 기록 목록 (기준 데이터)
    load_csv(path=None)    -> 엑셀 일괄 등록용 CSV 기록 목록
    save_data(records)     -> JSON·CSV·TXT·Pickle 저장 성공 여부
기록 형식(dict): id_num, name, birth_year, gender, height, weight, bmi, obesity_status
"""
from datetime import date

try:
    from .health_db import HealthDB  # main.py에서 modules 패키지로 불러올 때
except ImportError:
    from health_db import HealthDB   # modules 폴더에서 직접 실행할 때

# 사용자가 입력하는 항목 (bmi, obesity_status는 자동 계산)
INPUT_FIELDS = ("id_num", "name", "birth_year", "gender", "height", "weight")


class HealthManager:
    """건강 기록 목록의 등록·조회·검색·수정·삭제·통계를 담당한다."""

    def __init__(self, db=None):
        """모듈1을 통해 data/ 폴더의 기존 기록을 불러온다.

        Args:
            db: 모듈1의 HealthDB 객체 (생략하면 새로 만든다)
        """
        self.db = db or HealthDB()
        self.records = self._load()

    # ---------- BMI 계산 ----------
    @staticmethod
    def calc_bmi(height, weight):
        """BMI = 체중(kg) / (키(cm) / 100)², 소수 둘째 자리 반올림."""
        return round(weight / (height / 100) ** 2, 2)

    @staticmethod
    def get_grade(bmi):
        """BMI로 비만도를 판정한다 (대한비만학회 기준)."""
        if bmi < 18.5:
            return "저체중"
        if bmi < 23:
            return "정상"
        if bmi < 25:
            return "비만 전단계"
        if bmi < 30:
            return "1단계 비만"
        if bmi < 35:
            return "2단계 비만"
        return "3단계 비만"

    # ---------- 1. 신규 등록 및 중복 체크 ----------
    def add_record(self, id_num, name, birth_year, gender, height, weight):
        """UI에서 받은 값을 중복 검사 후 리스트와 파일에 추가한다.

        Args:
            id_num: 식별번호
            name: 이름
            birth_year: 출생연도
            gender: 성별 ("남" 또는 "여")
            height: 키(cm)
            weight: 몸무게(kg)
        Returns:
            추가된 기록(dict)
        Raises:
            ValueError: 입력값 오류 또는 식별번호 중복
            IOError: 파일 저장 실패
        """
        record = self._make_record(id_num, name, birth_year, gender, height, weight)
        if self.find_record(record["id_num"]) is not None:
            raise ValueError(f"이미 등록된 식별번호입니다: {record['id_num']}")
        self.records.append(record)
        self._save(undo=self.records.pop)
        return record

    def import_excel(self, path=None):
        """엑셀 CSV 파일의 기록을 중복 검사 후 리스트와 파일에 추가한다.

        이미 있는 식별번호는 중복으로 보고 넘어간다.

        Args:
            path: 엑셀에서 저장한 CSV 경로 (생략하면 모듈1의 data/health_data.csv)
        Returns:
            (추가 건수, 값이 잘못되어 건너뛴 건수)
        Raises:
            IOError: 파일 저장 실패
        """
        before = len(self.records)
        skipped = 0
        for row in self.db.load_csv(path):
            try:
                record = self._make_record(*(row.get(key) for key in INPUT_FIELDS))
            except ValueError:
                skipped += 1
                continue
            if self.find_record(record["id_num"]) is None:
                self.records.append(record)

        added = len(self.records) - before
        if added:
            def undo():
                del self.records[before:]
            self._save(undo)
        return added, skipped

    # ---------- 2. 조회 및 검색 ----------
    def get_all(self):
        """전체 기록 목록을 반환한다."""
        return list(self.records)

    def find_record(self, id_num):
        """식별번호로 기록 하나를 찾는다. 없으면 None."""
        id_num = str(id_num).strip()
        for record in self.records:
            if record["id_num"] == id_num:
                return record
        return None

    def search(self, keyword, field="all"):
        """이름 또는 식별번호에 검색어가 들어 있는 기록을 찾는다.

        Args:
            keyword: 검색어 (비어 있으면 전체 반환)
            field: "all"(이름+식별번호), "name"(이름), "id"(식별번호)
        """
        keyword = str(keyword).strip()
        if not keyword:
            return self.get_all()
        result = []
        for record in self.records:
            in_name = keyword in record["name"]
            in_id = keyword in record["id_num"]
            if (field == "name" and in_name) or (field == "id" and in_id) \
                    or (field == "all" and (in_name or in_id)):
                result.append(record)
        return result

    # ---------- 3. 수정 및 BMI 자동 재계산 ----------
    def update_record(self, id_num, name, birth_year, gender, height, weight):
        """기록을 수정하고 BMI·비만도를 다시 계산해 파일에 반영한다.

        Returns:
            수정된 기록(dict)
        Raises:
            ValueError: 없는 식별번호 또는 입력값 오류
            IOError: 파일 저장 실패
        """
        old = self._get_existing(id_num)
        index = self.records.index(old)
        new = self._make_record(old["id_num"], name, birth_year, gender, height, weight)
        self.records[index] = new
        self._save(undo=lambda: self.records.__setitem__(index, old))
        return new

    # ---------- 4. 삭제 ----------
    def delete_record(self, id_num):
        """선택한 기록을 삭제하고 파일에 반영한다. 저장 실패 시 삭제를 취소한다.

        Returns:
            삭제된 기록(dict)
        Raises:
            ValueError: 없는 식별번호
            IOError: 파일 저장 실패
        """
        record = self._get_existing(id_num)
        index = self.records.index(record)
        self.records.pop(index)
        self._save(undo=lambda: self.records.insert(index, record))
        return record

    # ---------- 5. 통계 산출 ----------
    def get_statistics(self):
        """전체 인원수, 평균 키·몸무게·BMI, 비만도별 인원을 계산한다.

        Returns:
            dict - count, avg_height, avg_weight, avg_bmi, grade_counts
            (기록이 없으면 평균은 0)
        """
        count = len(self.records)
        if count == 0:
            return {"count": 0, "avg_height": 0, "avg_weight": 0,
                    "avg_bmi": 0, "grade_counts": {}}

        grade_counts = {}
        for record in self.records:
            grade = record["obesity_status"]
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        return {
            "count": count,
            "avg_height": round(sum(r["height"] for r in self.records) / count, 1),
            "avg_weight": round(sum(r["weight"] for r in self.records) / count, 1),
            "avg_bmi": round(sum(r["bmi"] for r in self.records) / count, 2),
            "grade_counts": grade_counts,
        }

    # ---------- 내부 도우미 ----------
    def _load(self):
        """모듈1에서 저장된 기록을 불러온다. 값이 잘못된 기록과 중복 식별번호는 제외한다."""
        records = []
        for row in self.db.load_json():
            try:
                record = self._make_record(*(row.get(key) for key in INPUT_FIELDS))
            except (ValueError, AttributeError):
                continue
            if all(r["id_num"] != record["id_num"] for r in records):
                records.append(record)
        return records

    def _save(self, undo):
        """목록을 모듈1로 저장한다. 실패하면 undo로 변경을 되돌리고 IOError."""
        if not self.db.save_data(self.records):
            undo()
            raise IOError("파일 저장에 실패하여 작업을 취소했습니다.\n"
                          "파일이 엑셀 등 다른 프로그램에서 열려 있다면 닫고 다시 시도해 주세요.")

    def _make_record(self, id_num, name, birth_year, gender, height, weight):
        """값을 검사·변환하고 BMI·비만도를 계산해 기록(dict)을 만든다.

        Raises:
            ValueError: 빈 값, 숫자가 아닌 값, 0 이하의 값, 잘못된 성별·출생연도
        """
        id_num = str(id_num or "").strip()
        name = str(name or "").strip()
        gender = str(gender or "").strip()
        if not id_num or not name:
            raise ValueError("식별번호와 이름을 입력해 주세요.")
        if gender not in ("남", "여"):
            raise ValueError("성별은 '남' 또는 '여'로 입력해 주세요.")
        birth_year = self._to_birth_year(birth_year)
        height = self._to_positive(height, "키")
        weight = self._to_positive(weight, "몸무게")
        bmi = self.calc_bmi(height, weight)
        return {"id_num": id_num, "name": name, "birth_year": birth_year, "gender": gender,
                "height": height, "weight": weight, "bmi": bmi,
                "obesity_status": self.get_grade(bmi)}

    @staticmethod
    def _to_positive(value, label):
        """값을 0보다 큰 실수로 바꾼다. 바꿀 수 없으면 ValueError."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{label}에는 숫자를 입력해 주세요.") from None
        if not 0 < number < float("inf"):
            raise ValueError(f"{label}는 0보다 큰 숫자로 입력해 주세요.")
        return number

    @staticmethod
    def _to_birth_year(value):
        """출생연도를 정수로 바꾼다. 숫자가 아니거나 범위를 벗어나면 ValueError."""
        this_year = date.today().year
        try:
            year = int(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError("출생연도는 숫자로 입력해 주세요. 예) 2002") from None
        if not 1900 <= year <= this_year:
            raise ValueError(f"출생연도는 1900~{this_year} 사이로 입력해 주세요.")
        return year

    def _get_existing(self, id_num):
        """식별번호로 기록을 찾고, 없으면 ValueError."""
        record = self.find_record(id_num)
        if record is None:
            raise ValueError(f"해당 식별번호의 기록이 없습니다: {id_num}")
        return record