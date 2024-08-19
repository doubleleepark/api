import pymysql

def connect_db(config):
    """데이터베이스 연결 설정"""
    connection = pymysql.connect(host=config['host'],
                                 user=config['user'],
                                 password=config['password'],
                                 database=config['database'],
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

def insert_exhibitions(connection, exhibitions):
    """전시회 정보를 데이터베이스에 삽입"""
    with connection.cursor() as cursor:
        sql = """
        INSERT INTO exhibitions (name, latitude, longitude, start_date, end_date, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        for exhibition in exhibitions:
            name = exhibition[1]
            start_date, end_date = exhibition[2]
            latitude, longitude = exhibition[3]
            description = exhibition[4]
            cursor.execute(sql, (name, latitude, longitude, start_date, end_date, description))
        connection.commit()

# 데이터베이스 연결 설정
db_config = {
    'host': 'database-1.c588s0060coo.ap-northeast-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'restartart',
    'database': 'restartdb'
}

# 데이터베이스 연결
db_connection = connect_db(db_config)

# 전시회 정보
exhibitions = [
    ["https://ifh.cc/g/KtVo8L.jpg", "아르떼", ["2024-04-01", "2024-08-12"], [37.5119564733933, 127.088282780728], "끊임없이 절벽을 향해 물보라를 일으키는 파도, 거센 바람이 쉼 없이 불어오는 그 언덕의 끝에 그녀가 서 있다. Never Silence, 단 한번도 고요한 적 없었던 그녀의 삶에 대한 이야기가 시작된다."],
    ["https://ifh.cc/g/V7NpL0.jpg", "폭풍의 언덕에서", ["2024-04-01", "2024-08-12"], [37.5173319258532, 127.047377408384], "강릉은 밸리(VALLEY)라는 테마로 백두대간의 중추인 강원도와 강릉의 지역적 특성을 반영한 12개의 다래촐운 미디어아트 전시가 1,500평의 공간에서 시각적 강렬함과 더불어 감각적인 사운드, 품격있는 향기와 함께 몰입 경험을 제공"]
]

# 전시회 정보 삽입
insert_exhibitions(db_connection, exhibitions)