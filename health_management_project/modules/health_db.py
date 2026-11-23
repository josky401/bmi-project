# [AI 사용 주석]
# - AI 종류: Claude (Anthropic, Claude Opus 5.5)
# - 사용 목적: 요구서의 모듈2 기능(등록·중복 체크, 조회·검색, 수정·BMI 재계산, 삭제·파일 동기,
#   통계)을 본인이 작성한 모듈1(HealthDB, 코드 수정 없음)과 연결되도록 작성한 health_logic.py
#   전체 코드 생성 → 실행 코드와 주석 모두 AI가 작성함
# - 사용 프롬프트:
#   (1) "모듈2 health_logic.py (비즈니스로직) 핵심비즈니스규칙및 CRUD • 신규등록및중복체크: ..."
#       + 요구서의 예외처리·UX·코드 품질·제약사항 요구사항 전문 붙여넣음
#   (2) AI 사용 주석 예시를 붙여넣고 "이건 참고용 이고 이런식으로 써넣어야해"
#   (3) 이름·학번 기입, "db는 필요없고 로직만주면돼고 저거 주석에 공백이너무 많아 다듬어줘"
#   (4) "혹시 로직만해서 만든거 맞지 300줄이나 돼서"
#   (5) 모듈2 기능 목록을 다시 붙여넣고 "요거만 코드짜줘 다른코드는 일절 넣지말고"
#   (6) 모듈1 health_db.py 파일을 올리고 "모듈 1이고 로직 파일하고 연결할수있게 코드를 짜줘"
#   (7) 프로젝트 폴더 구조 이미지를 올리고 "모듈1 문제있는코드있으면 수정해서 로직이랑 연동시키고
#       파일 구조체 이렇게 돼있어서 모듈1의 저장됀 파일 위치를 가져오는형식이야"
#   (8) "음 못찾으면 모듈만만들어주고 db ai 주석 내가 처음준 db.py 주석써줘"
#   (9) 처음 모듈1 파일을 다시 올리고 "내가 말한건 이거였어"
# - 본인 수정: (직접 고친 부분이 있으면 적기)
# - 사용한 사람: 조하늘 (202611844)
# - 날짜: 2026-11-24
import json
import csv
import pickle

class HealthDB:
    def __init__(self):
        self.json_file = "health_management_project\\data\\health_data.json"
        self.csv_file = "health_management_project\\data\\health_data.csv"
        self.txt_file = "health_management_project\\data\\health_data.txt"
        self.pkl_file = "health_management_project\\data\\health_data.pkl"
        
    def load_data(self):
        with open(self.json_file, "r", encoding="utf-8") as jf:
            jsdata = json.load(jf)
        
        with open(self.csv_file, "r", encoding="utf-8") as cf:
            csvdata = list(csv.DictReader(cf))

        with open(self.txt_file, "r", encoding="utf-8") as tf:
            txtdata = [line.strip().split(",") for line in tf.readlines()]

        with open(self.pkl_file, "rb") as pf:
            pkldata = pickle.load(pf)

        return jsdata, csvdata, txtdata, pkldata

    def save_data(self, jsdata, csvdata, txtdata, pkldata):
        with open(self.json_file, "w", encoding="utf-8") as jf:
            json.dump(jsdata, jf, ensure_ascii=False, indent=4)

        with open(self.csv_file, "w", encoding="utf-8", newline="") as cf:
            writer = csv.DictWriter(cf, fieldnames=csvdata[0].keys())
            writer.writeheader()
            writer.writerows(csvdata)

        with open(self.txt_file, "w", encoding="utf-8") as tf:
            for row in txtdata:
                tf.write(",".join(row) + "\n")

        with open(self.pkl_file, "wb") as pf:
            pickle.dump(pkldata, pf)

#AI 사용
if __name__ == "__main__":
    # 1. 테스트용 원본 데이터 (딕셔너리 리스트)
    records = [
        {"id_num": "H001", "name": "김철수", "birth_year": 2002, "gender": "남", "height": 175.0, "weight": 70.0, "bmi": 22.86, "obesity_status": "정상"},
        {"id_num": "H002", "name": "이영희", "birth_year": 2004, "gender": "여", "height": 162.5, "weight": 54.0, "bmi": 20.44, "obesity_status": "정상"}
    ]

    print("원본 데이터:", records)
    db = HealthDB() # 이미 구현된 클래스

    # 2. TXT 저장을 위한 문자열 리스트 변환 (for 축약문법 활용)
    txt_rows = [
        [r["id_num"], r["name"], str(r["birth_year"]), r["gender"], str(r["height"]), str(r["weight"]), str(r["bmi"]), r["obesity_status"]]
        for r in records
    ]

    # 3. 저장 및 로드 검증
    db.save_data(records, records, txt_rows, records)
    jsdata, csvdata, txtdata, pkldata = db.load_data()

    # 4. CSV에서 문자열로 읽은 숫자/수치형 데이터 복원
    for row in csvdata:
        row["birth_year"] = int(row["birth_year"])
        row["height"] = float(row["height"])
        row["weight"] = float(row["weight"])
        row["bmi"] = float(row["bmi"])

    # 5. TXT에서 읽은 리스트를 원본과 같은 딕셔너리로 복원
    txtdata = [
        {
            "id_num": row[0],
            "name": row[1],
            "birth_year": int(row[2]),
            "gender": row[3],
            "height": float(row[4]),
            "weight": float(row[5]),
            "bmi": float(row[6]),
            "obesity_status": row[7]
        }
        for row in txtdata
    ]

    # 6. 포맷별 결과 비교 출력
    results = {
        "JSON": jsdata,
        "CSV": csvdata,
        "TXT": txtdata,
        "PKL": pkldata
    }

    for file_type, loaded in results.items():
        print(f"\n{file_type}에서 읽은 데이터:", loaded)
        print("원본과 일치:", records == loaded)