import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# UTF-8 출력 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 디렉토리 생성
os.makedirs('data', exist_ok=True)

# 한글 데이터 설정
regions = ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구',
           '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구',
           '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구']

building_types = ['아파트', '단독주택', '오피스텔', '상가', '주상복합', '다세대주택', '빌라']
transaction_types = ['매매', '전세', '월세', '경매', '공매']

np.random.seed(42)

# 1. 월별 거래현황 (2023-01 ~ 2024-12)
print("월별 거래현황 생성 중...")
dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='ME')
monthly_data = []

for date in dates:
    for region in regions:
        for building_type in building_types:
            monthly_data.append({
                '거래년월': date.strftime('%Y-%m'),
                '지역명': region,
                '건물유형': building_type,
                '거래건수': np.random.randint(10, 500),
                '거래액(억원)': np.random.uniform(100, 5000),
                '평균가격(만원)': np.random.uniform(3000, 100000)
            })

df_monthly = pd.DataFrame(monthly_data)
df_monthly.to_csv('data/monthly_transaction.csv', index=False, encoding='utf-8-sig')
print(f"✓ monthly_transaction.csv 생성 ({len(df_monthly)} 행)")

# 2. 지역별 상세 거래정보
print("지역별 상세 거래정보 생성 중...")
detailed_data = []
base_date = datetime(2024, 1, 1)

for i in range(3000):
    transaction_date = base_date + timedelta(days=np.random.randint(0, 365))
    region = np.random.choice(regions)

    # 지역에 따른 기본 가격대 설정
    price_multiplier = np.random.uniform(0.8, 1.5)

    detailed_data.append({
        '거래일자': transaction_date.strftime('%Y-%m-%d'),
        '지역명': region,
        '지역상세': f"{region} {np.random.randint(1, 20)}동",
        '건물유형': np.random.choice(building_types),
        '거래유형': np.random.choice(transaction_types),
        '거래금액(만원)': int(np.random.lognormal(mean=11, sigma=0.8) * price_multiplier),
        '보증금(만원)': int(np.random.lognormal(mean=10, sigma=0.7)) if np.random.random() > 0.5 else 0,
        '월세(만원)': int(np.random.uniform(30, 300)) if np.random.random() > 0.7 else 0,
        '면적(㎡)': np.random.uniform(20, 200),
        '층수': np.random.randint(-2, 50),
        '준공연도': np.random.randint(1980, 2024),
        '거래중개': np.random.choice(['직거래', '중개', '경매'])
    })

df_detailed = pd.DataFrame(detailed_data)
df_detailed.to_csv('data/detailed_transaction.csv', index=False, encoding='utf-8-sig')
print(f"✓ detailed_transaction.csv 생성 ({len(df_detailed)} 행)")

# 3. 건물유형별 분석 데이터
print("건물유형별 분석 데이터 생성 중...")
building_type_data = []

for building_type in building_types:
    for month in pd.date_range('2023-01', '2024-12', freq='ME'):
        building_type_data.append({
            '거래년월': month.strftime('%Y-%m'),
            '건물유형': building_type,
            '거래건수': np.random.randint(50, 800),
            '거래액(억원)': np.random.uniform(200, 10000),
            '평균거래가(만원)': np.random.uniform(5000, 150000),
            '가격상승률(%)': np.random.uniform(-5, 10)
        })

df_building = pd.DataFrame(building_type_data)
df_building.to_csv('data/building_type_analysis.csv', index=False, encoding='utf-8-sig')
print(f"✓ building_type_analysis.csv 생성 ({len(df_building)} 행)")

# 4. 거래유형별 분석 데이터
print("거래유형별 분석 데이터 생성 중...")
transaction_type_data = []

for transaction_type in transaction_types:
    for month in pd.date_range('2023-01', '2024-12', freq='ME'):
        transaction_type_data.append({
            '거래년월': month.strftime('%Y-%m'),
            '거래유형': transaction_type,
            '거래건수': np.random.randint(100, 1200),
            '거래액(억원)': np.random.uniform(300, 15000),
            '평균거래가(만원)': np.random.uniform(3000, 120000),
            '전월대비(%)': np.random.uniform(-3, 5)
        })

df_transaction = pd.DataFrame(transaction_type_data)
df_transaction.to_csv('data/transaction_type_analysis.csv', index=False, encoding='utf-8-sig')
print(f"✓ transaction_type_analysis.csv 생성 ({len(df_transaction)} 행)")

# 5. 지역별 월별 요약 (크로스탭 형식)
print("지역별 월별 요약 생성 중...")
regional_monthly_data = []

for region in regions:
    for month in pd.date_range('2023-01', '2024-12', freq='ME'):
        regional_monthly_data.append({
            '지역명': region,
            '거래년월': month.strftime('%Y-%m'),
            '거래건수': np.random.randint(30, 400),
            '거래액(억원)': np.random.uniform(100, 3000),
            '평균면적(㎡)': np.random.uniform(40, 120),
            '평균가격(만원)': np.random.uniform(5000, 100000)
        })

df_regional_monthly = pd.DataFrame(regional_monthly_data)
df_regional_monthly.to_csv('data/regional_monthly_summary.csv', index=False, encoding='utf-8-sig')
print(f"✓ regional_monthly_summary.csv 생성 ({len(df_regional_monthly)} 행)")

# 6. 시계열 가격지수
print("시계열 가격지수 생성 중...")
timeseries_data = []
base_index = 100

for i, month in enumerate(pd.date_range('2023-01', '2024-12', freq='ME')):
    base_index = base_index * (1 + np.random.uniform(-0.02, 0.03))
    timeseries_data.append({
        '거래년월': month.strftime('%Y-%m'),
        '종합지수': base_index,
        '매매지수': base_index * np.random.uniform(0.95, 1.05),
        '전세지수': base_index * np.random.uniform(0.92, 1.08),
        '월세지수': base_index * np.random.uniform(0.90, 1.10)
    })

df_timeseries = pd.DataFrame(timeseries_data)
df_timeseries.to_csv('data/price_index_timeseries.csv', index=False, encoding='utf-8-sig')
print(f"✓ price_index_timeseries.csv 생성 ({len(df_timeseries)} 행)")

# 7. 강남/강북/강동/강서 분권역 분석
print("분권역별 분석 데이터 생성 중...")
gangnam_regions = ['강남구', '강동구', '서초구', '송파구']
gangbuk_regions = ['강북구', '도봉구', '노원구', '성북구', '중랑구']
gangdong_regions = ['강동구', '송파구']
gangwest_regions = ['강서구', '양천구', '영등포구', '마포구']

division_data = []
for month in pd.date_range('2023-01', '2024-12', freq='ME'):
    for division, region_list in [('강남권', gangnam_regions), ('강북권', gangbuk_regions),
                                   ('강동권', gangdong_regions), ('강서권', gangwest_regions)]:
        division_data.append({
            '거래년월': month.strftime('%Y-%m'),
            '권역': division,
            '거래건수': np.random.randint(100, 600),
            '거래액(억원)': np.random.uniform(300, 8000),
            '평균가격(만원)': np.random.uniform(5000, 120000),
            '재계약률(%)': np.random.uniform(20, 80)
        })

df_division = pd.DataFrame(division_data)
df_division.to_csv('data/division_analysis.csv', index=False, encoding='utf-8-sig')
print(f"✓ division_analysis.csv 생성 ({len(df_division)} 행)")

# 8. 준공연도별 거래현황
print("준공연도별 거래현황 생성 중...")
construction_data = []
decades = list(range(1980, 2024, 5)) + [2024]

for decade in decades:
    for month in pd.date_range('2023-01', '2024-12', freq='ME'):
        construction_data.append({
            '거래년월': month.strftime('%Y-%m'),
            '준공연도': decade,
            '거래건수': np.random.randint(20, 300),
            '거래액(억원)': np.random.uniform(50, 2000),
            '평균가격(만원)': np.random.uniform(2000, 80000)
        })

df_construction = pd.DataFrame(construction_data)
df_construction.to_csv('data/construction_year_analysis.csv', index=False, encoding='utf-8-sig')
print(f"✓ construction_year_analysis.csv 생성 ({len(df_construction)} 행)")

print("\n" + "="*50)
print("✅ 모든 데이터 생성 완료!")
print("="*50)
print(f"\n생성된 파일들 (data/ 폴더):")
print("  1. monthly_transaction.csv - 월별 거래현황")
print("  2. detailed_transaction.csv - 지역별 상세 거래정보")
print("  3. building_type_analysis.csv - 건물유형별 분석")
print("  4. transaction_type_analysis.csv - 거래유형별 분석")
print("  5. regional_monthly_summary.csv - 지역별 월별 요약")
print("  6. price_index_timeseries.csv - 시계열 가격지수")
print("  7. division_analysis.csv - 분권역별 분석")
print("  8. construction_year_analysis.csv - 준공연도별 분석")
print(f"\n총 {len(df_monthly) + len(df_detailed) + len(df_building) + len(df_transaction) + len(df_regional_monthly) + len(df_timeseries) + len(df_division) + len(df_construction)} 행의 데이터 생성됨")
