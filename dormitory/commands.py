import click
import random
from dormitory import app, db
from dormitory.models import Dorm, Room, Manager, Student, Fix, Visitor


@app.cli.command()
@click.option("--drop", is_flag=True, help="Create after drop.")
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo("Database initialized.")


@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    for i in range(1, 11):
        levels = random.randint(5, 20)
        d = Dorm(id=i, levels=levels, gender=random.choice(["男", "女"]))
        db.session.add(d)

        spaces = random.choice([4, 6])

        for j in range(1, levels + 1):
            for k in range(1, 6):
                r = Room(id=f"{i}-{j:0>2}0{k}", dorm_id=i, level=j, spaces=spaces)
                db.session.add(r)

    managers = [
        {
            "id": "10234",
            "name": "史听云",
            "gender": "女",
            "age": 30,
            "phone": "13912345678",
            "dorm_id": 1,
        },
        {
            "id": "34678",
            "name": "耿文霞",
            "gender": "女",
            "age": 28,
            "phone": "13012435678",
            "dorm_id": 2,
        },
        {
            "id": "41301",
            "name": "毛雅安",
            "gender": "女",
            "age": 32,
            "phone": "13345678901",
            "dorm_id": 3,
        },
        {
            "id": "48624",
            "name": "钟同化",
            "gender": "男",
            "age": 38,
            "phone": "13145735678",
            "dorm_id": 4,
        },
        {
            "id": "55966",
            "name": "陈弘坚",
            "gender": "男",
            "age": 29,
            "phone": "13245678901",
            "dorm_id": 5,
        },
        {
            "id": "63289",
            "name": "邓慧秀",
            "gender": "女",
            "age": 31,
            "phone": "13512345678",
            "dorm_id": 6,
        },
        {
            "id": "70612",
            "name": "蒋文彬",
            "gender": "男",
            "age": 33,
            "phone": "13412345678",
            "dorm_id": 7,
        },
        {
            "id": "77945",
            "name": "李慧娟",
            "gender": "女",
            "age": 35,
            "phone": "13712345678",
            "dorm_id": 8,
        },
        {
            "id": "85278",
            "name": "张同化",
            "gender": "男",
            "age": 34,
            "phone": "13812345678",
            "dorm_id": 9,
        },
        {
            "id": "92601",
            "name": "赵文彬",
            "gender": "男",
            "age": 36,
            "phone": "13612345678",
            "dorm_id": 10,
        },
    ]

    for manager in managers:
        m = Manager(**manager)
        m.set_password("12345678")
        db.session.add(m)

    students = [
        {
            "id": "20180001",
            "name": "常阳炎",
            "age": 20,
            "phone": "12312312312",
            "major": "计算机科学与技术",
            "grade": 2018,
            "room_id": "2-0501",
        },
        {
            "id": "20180002",
            "name": "寿丽佳",
            "age": 19,
            "phone": "12312312312",
            "major": "理论物理",
            "grade": 2018,
            "room_id": "1-0101",
        },
        {
            "id": "20180003",
            "name": "李秀静",
            "age": 20,
            "phone": "12312312312",
            "major": "化学",
            "grade": 2018,
            "room_id": "1-0301",
        },
        {
            "id": "20180004",
            "name": "曹滢天",
            "age": 20,
            "phone": "12312312312",
            "major": "生物",
            "grade": 2018,
            "room_id": "1-0301",
        },
        {
            "id": "20190001",
            "name": "杨晨",
            "age": 18,
            "phone": "12312312312",
            "major": "化学",
            "grade": 2019,
            "room_id": "3-0405",
        },
        {
            "id": "20190002",
            "name": "张宇",
            "age": 19,
            "phone": "12312312312",
            "major": "生物",
            "grade": 2019,
            "room_id": "4-0202",
        },
    ]

    for student in students:
        s = Student(**student)
        s.set_password("12345678")
        db.session.add(s)

    fixes = [
        {
            "id": 1,
            "student_id": "20180002",
            "room_id": "1-0201",
            "category": "电工类",
            "content": "灯坏了",
            "picture": "/static/upload/灯.jfif",
            "submit_time": "2021-09-01 12:00:00",
            "status": "未处理",
        },
        {
            "id": 2,
            "student_id": "20180003",
            "room_id": "1-0301",
            "category": "水工类",
            "content": "水管堵塞了",
            "picture": "/static/upload/堵塞.jpg",
            "submit_time": "2021-10-02 12:00:00",
            "status": "未处理",
        },
    ]

    for fix in fixes:
        f = Fix(**fix)
        db.session.add(f)

    visitors = [
        {
            "id": 1,
            "student_id": "20180001",
            "room_id": "2-0501",
            "name": "羿茂德",
            "gender": "男",
            "phone": "13212331231",
            "reason": "探望",
            "visit_time": "2022-01-01 12:00:00",
            "leave_time": "2022-01-01 14:00:00",
        }
    ]

    for visitor in visitors:
        v = Visitor(**visitor)
        db.session.add(v)

    for r in Room.query.all():
        r.residents = len(r.students)

    for d in Dorm.query.all():
        d.rooms = len(d.apartments)
        d.left_residents = sum([r.spaces - r.residents for r in d.apartments])

    db.session.commit()
    click.echo("Done.")
