import os

from dormitory import app, db
from dormitory.models import Dorm, Room, Manager, Student, Fix, Visitor, Move

from flask import render_template, request, url_for, redirect, flash
from flask_wtf import FlaskForm, CSRFProtect
from flask_login import login_user, login_required, logout_user, current_user
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    FileField,
    TextAreaField,
    DateTimeLocalField,
)
from wtforms.validators import DataRequired, Length

csrf = CSRFProtect(app)


@app.route("/index.html", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Dorm.query.paginate(page=page, per_page=5)
    dorms = pagination.items

    titles = [
        ("id", "#"),
        ("levels", "楼层数"),
        ("rooms", "总房间数"),
        ("left_residents", "空余床位数"),
        ("gender", "性别"),
    ]

    return render_template(
        "index.html",
        pagination=pagination,
        dorms=dorms,
        titles=titles,
    )


@app.route("/dorm/<int:dorm_id>")
def dorm_info(dorm_id):
    dorm = Dorm.query.get_or_404(dorm_id)
    managers = []
    for manager in dorm.managers:
        managers.append(
            {
                "id": manager.id,
                "name": manager.name,
                "gender": manager.gender,
                "age": manager.age,
                "phone": manager.phone,
            }
        )
    title = [
        ("id", "工号"),
        ("name", "姓名"),
        ("gender", "性别"),
        ("age", "年龄"),
        ("phone", "电话"),
    ]
    page = request.args.get("page", 1, type=int)
    pagination = Room.query.filter_by(dorm_id=dorm_id).paginate(page=page, per_page=5)
    rooms = []
    for room in pagination.items:
        rooms.append(
            {
                "id": room.id,
                "level": room.level,
                "spaces": room.spaces,
                "residents": room.residents,
            }
        )
    room_title = [
        ("id", "房间号"),
        ("level", "楼层"),
        ("spaces", "床位数"),
        ("residents", "入住人数"),
    ]
    return render_template(
        "dorm.html",
        dorm=dorm.id,
        managers=managers,
        title=title,
        rooms=rooms,
        room_title=room_title,
        pagination=pagination,
    )


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(1, 20)])
    password = PasswordField("密码", validators=[DataRequired(), Length(8, 150)])
    manager = BooleanField("管理员登录")
    submit = SubmitField("登录")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        manager = form.manager.data

        if manager:
            user = Manager.query.filter_by(id=username).first()
        else:
            user = Student.query.filter_by(id=username).first()

        if user is None or not user.validate_password(password):
            flash("用户名或密码错误!", category="danger")
            return redirect(url_for("login"))

        login_user(user)
        flash(f"登录成功!", category="success")
        if password == "12345678":
            flash("您使用的是默认密码，请尽快修改!", category="warning")
        return redirect(url_for("index"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("退出成功！", category="info")
    return redirect(url_for("index"))


class SettingsForm(FlaskForm):
    phone = StringField("电话", validators=[Length(11, 11)])
    password = PasswordField("新密码", validators=[Length(0) or Length(8, 150)])
    submit = SubmitField("保存设置")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        try:
            current_user.phone = form.phone.data
            if form.password.data:
                current_user.set_password(form.password.data)
            db.session.commit()
            flash(f"设置已保存！", category="success")
        except:
            db.session.rollback()
            flash("出现错误，保存失败！", category="danger")
        return redirect(url_for("settings"))
    form.phone.data = current_user.phone
    return render_template("settings.html", form=form)


class MoveForm(FlaskForm):
    room = SelectField("转入房间号", choices=[], validators=[DataRequired()])
    reason = TextAreaField("转宿原因", validators=[DataRequired(), Length(1, 100)])
    submit = SubmitField("确认提交")


@app.route("/info", methods=["GET", "POST"])
@login_required
def info():
    if current_user.__class__ == Manager:
        return redirect(url_for("index"))
    room = Room.query.get(current_user.room_id)
    students = []
    for student in room.students:
        students.append(
            {
                "id": student.id,
                "name": student.name,
                "age": student.age,
                "phone": student.phone,
                "major": student.major,
                "grade": student.grade,
            }
        )
    title = [
        ("id", "学号"),
        ("name", "姓名"),
        ("age", "年龄"),
        ("phone", "电话"),
        ("major", "专业"),
        ("grade", "年级"),
    ]

    move = Move.query.filter_by(student_id=current_user.id)
    move_title = [
        ("id", "申请编号"),
        ("original_room_id", "原房间号"),
        ("target_room_id", "目标房间号"),
        ("reason", "原因"),
        ("status", "状态"),
    ]

    available_rooms = (
        Room.query.filter_by(dorm_id=room.dorm_id)
        .filter(Room.id != room.id)
        .filter(Room.spaces - Room.residents > 0)
        .all()
    )
    form = MoveForm()
    form.room.choices = [(r.id, r.id) for r in available_rooms]

    if form.validate_on_submit():
        if move.filter_by(status="未处理").first():
            flash("您有未审核处理的转宿申请，请等待处理！", category="warning")
            return redirect(url_for("info"))
        try:
            move = Move(
                student_id=current_user.id,
                original_room_id=current_user.room_id,
                target_room_id=form.room.data,
                reason=form.reason.data,
            )
            db.session.add(move)
            db.session.commit()
            flash("提交成功！", category="info")
        except:
            db.session.rollback()
            flash("出现错误，提交失败！", category="danger")
        return redirect(url_for("info"))

    return render_template(
        "info.html",
        room=room,
        students=students,
        title=title,
        form=form,
        move=move.all(),
        move_title=move_title,
    )


class ReportForm(FlaskForm):
    category = SelectField(
        "报修类型",
        choices=[
            ("电工类", "电工类"),
            ("水工类", "水工类"),
            ("瓦工类", "瓦工类"),
            ("其他", "其他"),
        ],
        validators=[DataRequired()],
    )
    content = TextAreaField("内容", validators=[DataRequired(), Length(1, 100)])
    picture = FileField("图片")
    submit = SubmitField("提交")


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if current_user.__class__ == Manager:
        return redirect(url_for("index"))
    form = ReportForm()
    if form.validate_on_submit():
        file = form.picture.data
        file.save(os.path.join(os.getcwd(), f"dormitory/static/upload/{file.filename}"))
        try:
            fix = Fix(
                student_id=current_user.id,
                room_id=current_user.room_id,
                category=form.category.data,
                content=form.content.data,
                picture=f"/static/upload/{file.filename}",
            )
            db.session.add(fix)
            db.session.commit()
            flash("报修已提交！", category="info")
        except:
            db.session.rollback()
            flash("出现错误，提交失败！", category="danger")
        return redirect(url_for("report"))

    page = request.args.get("page", 1, type=int)
    pagination = Fix.query.filter_by(student_id=current_user.id).paginate(
        page=page, per_page=5
    )
    fixes = []
    for fix in pagination.items:
        fixes.append(
            {
                "id": fix.id,
                "room_id": fix.room_id,
                "category": fix.category,
                "content": fix.content,
                "submit_time": fix.submit_time,
                "status": fix.status,
            }
        )
    title = [
        ("id", "报修编号"),
        ("room_id", "房间号"),
        ("category", "类别"),
        ("content", "内容"),
        ("submit_time", "提交时间"),
        ("status", "状态"),
    ]
    return render_template(
        "report.html", form=form, fix=fixes, title=title, pagination=pagination
    )


class VisitForm(FlaskForm):
    name = StringField("访客姓名", validators=[DataRequired(), Length(1, 20)])
    gender = SelectField("访客性别", choices=[("男", "男"), ("女", "女")])
    phone = StringField("访客电话", validators=[DataRequired(), Length(11, 11)])
    time = DateTimeLocalField(
        "访问时间", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    reason = TextAreaField("来访原因", validators=[DataRequired(), Length(1, 100)])
    submit = SubmitField("确认")


@app.route("/visit", methods=["GET", "POST"])
@login_required
def visit():
    if current_user.__class__ == Manager:
        return redirect(url_for("index"))
    form = VisitForm()
    if form.validate_on_submit():
        try:
            visitor = Visitor(
                student_id=current_user.id,
                room_id=current_user.room_id,
                name=form.name.data,
                gender=form.gender.data,
                phone=form.phone.data,
                reason=form.reason.data,
                visit_time=form.time.data,
            )
            db.session.add(visitor)
            db.session.commit()
            flash("访客已登记！", category="info")
            return redirect(url_for("visit"))
        except:
            db.session.rollback()
            flash("出现错误，提交失败！", category="danger")

    page = request.args.get("page", 1, type=int)
    pagination = Visitor.query.filter_by(student_id=current_user.id).paginate(
        page=page, per_page=5
    )
    visitors = []
    for visitor in pagination.items:
        visitors.append(
            {
                "id": visitor.id,
                "name": visitor.name,
                "room_id": visitor.room_id,
                "gender": visitor.gender,
                "phone": visitor.phone,
                "visit_time": visitor.visit_time,
                "leave_time": visitor.leave_time,
            }
        )
    title = [
        ("id", "访客编号"),
        ("name", "访客姓名"),
        ("room_id", "房间号"),
        ("gender", "性别"),
        ("phone", "电话"),
        ("visit_time", "访问时间"),
        ("leave_time", "离开时间"),
    ]

    return render_template(
        "visit.html", form=form, visitor=visitors, title=title, pagination=pagination
    )


class VisitorLeaveForm(FlaskForm):
    submit = SubmitField("已离开")


@app.route("/visitor/<int:visitor_id>", methods=["GET", "POST"])
@login_required
def visitor_info(visitor_id):
    if current_user.__class__ == Manager:
        return redirect(url_for("index"))
    visitor = Visitor.query.get_or_404(visitor_id)
    if visitor.student_id != current_user.id:
        return redirect(url_for("index"))

    form = VisitorLeaveForm()
    if form.validate_on_submit():
        try:
            visitor.leave_time = db.func.now()
            db.session.commit()
            flash("已登记离开！", category="info")
        except:
            db.session.rollback()
            flash("出现错误，登记失败！", category="danger")
        return redirect(url_for("visitor_info", visitor_id=visitor_id))

    return render_template("visitor.html", visitor=visitor, form=form)


@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    dorm_id = current_user.dorm_id
    dorm = Dorm.query.get(dorm_id)
    page = request.args.get("page", 1, type=int)
    pagination = Room.query.filter_by(dorm_id=dorm_id).paginate(page=page, per_page=5)
    rooms = []
    for room in pagination.items:
        rooms.append(
            {
                "id": room.id,
                "level": room.level,
                "spaces": room.spaces,
                "residents": room.residents,
            }
        )
    title = [
        ("id", "房间号"),
        ("level", "楼层"),
        ("spaces", "床位数"),
        ("residents", "入住人数"),
    ]

    move_page = request.args.get("move_page", 1, type=int)
    move_pagination = (
        Move.query.join(Student)
        .join(Room)
        .filter(Room.dorm_id == dorm_id)
        .paginate(page=move_page, per_page=5)
    )
    moves = []
    for move in move_pagination.items:
        moves.append(
            {
                "id": move.id,
                "student_id": move.student_id,
                "original_room_id": move.original_room_id,
                "target_room_id": move.target_room_id,
                "reason": move.reason,
                "submit_time": move.submit_time,
                "status": move.status,
            }
        )
    move_title = [
        ("id", "申请编号"),
        ("student_id", "学号"),
        ("original_room_id", "原房间号"),
        ("target_room_id", "目标房间号"),
        ("reason", "原因"),
        ("submit_time", "提交时间"),
        ("status", "状态"),
    ]
    return render_template(
        "manage.html",
        dorm=dorm,
        rooms=rooms,
        title=title,
        pagination=pagination,
        moves=moves,
        move_title=move_title,
        move_pagination=move_pagination,
    )


class RoomForm(FlaskForm):
    id = StringField("房间号", validators=[DataRequired()])
    level = StringField("楼层", validators=[DataRequired()])
    spaces = StringField("床位数", validators=[DataRequired()])
    submit = SubmitField("修改")
    delete = SubmitField("删除")


@app.route("/room/<room_id>", methods=["GET", "POST"])
@login_required
def room_info(room_id):
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    room = Room.query.get_or_404(room_id)
    if room.dorm_id != current_user.dorm_id:
        return redirect(url_for("index"))
    form = RoomForm()
    if form.validate_on_submit():
        if form.delete.data:
            if room.residents > 0:
                flash("房间内有学生，无法删除！", category="danger")
                return redirect(url_for("room_info", room_id=room_id))
            try:
                for fix in room.fixes:
                    db.session.delete(fix)
                db.session.delete(room)
                db.session.commit()
                flash("删除成功！", category="info")
                return redirect(url_for("manage"))
            except:
                db.session.rollback()
                flash("出现错误，删除失败！", category="danger")
        if form.submit.data:
            if room.residents > int(form.spaces.data):
                flash("床位数不足，修改失败！", category="danger")
                return redirect(url_for("room_info", room_id=room_id))
            try:
                room.id = form.id.data
                room.level = form.level.data
                room.spaces = int(form.spaces.data)
                db.session.commit()
                flash("修改成功！", category="info")
            except:
                db.session.rollback()
                flash("出现错误，修改失败！", category="danger")
        return redirect(url_for("room_info", room_id=room_id))
    form.id.data = room.id
    form.level.data = room.level
    form.spaces.data = room.spaces

    students = []
    for student in room.students:
        students.append(
            {
                "id": student.id,
                "name": student.name,
                "age": student.age,
                "phone": student.phone,
                "major": student.major,
                "grade": student.grade,
            }
        )
    title = [
        ("id", "学号"),
        ("name", "姓名"),
        ("age", "年龄"),
        ("phone", "电话"),
        ("major", "专业"),
        ("grade", "年级"),
    ]
    return render_template(
        "room_info.html", room=room, students=students, title=title, form=form
    )


class StudentForm(FlaskForm):
    id = StringField("学号", validators=[DataRequired()])
    name = StringField("姓名", validators=[DataRequired()])
    age = StringField("年龄", validators=[DataRequired()])
    phone = StringField("电话", validators=[DataRequired(), Length(11, 11)])
    major = StringField("专业", validators=[DataRequired()])
    grade = StringField("年级", validators=[DataRequired()])
    submit = SubmitField("确定添加")


@app.route("/room/<room_id>/student", methods=["GET", "POST"])
@login_required
def new_student(room_id):
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    room = Room.query.get_or_404(room_id)
    if room.dorm_id != current_user.dorm_id:
        return redirect(url_for("index"))
    if room.spaces - room.residents < 1:
        flash("房间床位不足！", category="danger")
        return redirect(url_for("room_info", room_id=room_id))
    form = StudentForm()
    if form.validate_on_submit():
        if Student.query.get(form.id.data):
            flash("学号已存在！添加失败", category="danger")
            return redirect(url_for("new_student", room_id=room_id))
        try:
            student = Student(
                id=form.id.data,
                name=form.name.data,
                age=int(form.age.data),
                phone=form.phone.data,
                major=form.major.data,
                grade=form.grade.data,
                room_id=room_id,
            )
            student.set_password("12345678")
            db.session.add(student)
            db.session.commit()
            flash("添加成功！", category="info")
        except:
            db.session.rollback()
            flash("出现错误，添加失败！", category="danger")
        return redirect(url_for("room_info", room_id=room_id))
    return render_template("new_student.html", room=room, form=form)


@app.route("/student/<student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    student = Student.query.get_or_404(student_id)
    room = Room.query.get(student.room_id)
    if room.dorm_id != current_user.dorm_id:
        return redirect(url_for("index"))
    try:
        for fix in student.fixes:
            db.session.delete(fix)
        for visitor in student.visitors:
            db.session.delete(visitor)
        for move in student.moves:
            db.session.delete(move)
        db.session.delete(student)
        db.session.commit()
        flash("删除成功！", category="info")
    except:
        db.session.rollback()
        flash("出现错误，删除失败！", category="danger")
    return redirect(url_for("room_info", room_id=room.id))


class MoveManageForm(FlaskForm):
    agree = SubmitField("同意")
    reject = SubmitField("拒绝")


@app.route("/move/<int:move_id>", methods=["GET", "POST"])
@login_required
def move_info(move_id):
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    move = Move.query.get_or_404(move_id)
    student = Student.query.get(move.student_id)
    if student.room.dorm_id != current_user.dorm_id:
        return redirect(url_for("index"))
    form = MoveManageForm()
    if form.validate_on_submit():
        if form.reject.data:
            try:
                move.status = "已拒绝"
                db.session.commit()
                flash("已拒绝！", category="info")
            except:
                db.session.rollback()
                flash("出现错误，拒绝失败！", category="danger")

        if form.agree.data:
            room = Room.query.get(move.target_room_id)
            if room.spaces - room.residents < 1:
                flash("目标房间床位不足！", category="danger")
                return redirect(url_for("move_info", move_id=move_id))
            try:
                move.status = "已同意"
                student.room_id = move.target_room_id
                db.session.commit()
                flash("已同意！", category="info")
            except:
                db.session.rollback()
                flash("出现错误，同意失败！", category="danger")

        return redirect(url_for("move_info", move_id=move_id))
    return render_template("move.html", move=move, student=student, form=form)


class NewRoomForm(FlaskForm):
    id = StringField("房间号", validators=[DataRequired()])
    level = StringField("楼层", validators=[DataRequired()])
    spaces = StringField("床位数", validators=[DataRequired()])
    submit = SubmitField("确定添加")


@app.route("/manage/<int:dorm_id>", methods=["GET", "POST"])
@login_required
def new_room(dorm_id):
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    if current_user.dorm_id != dorm_id:
        return redirect(url_for("index"))
    form = NewRoomForm()
    if form.validate_on_submit():
        if Room.query.get(form.id.data):
            flash("房间号已存在！添加失败", category="danger")
            return redirect(url_for("new_room", dorm_id=dorm_id))
        if Dorm.query.get(dorm_id).levels < int(form.level.data):
            flash("楼层数不足！添加失败", category="danger")
            return redirect(url_for("new_room", dorm_id=dorm_id))
        if not form.spaces.data.isdigit():
            flash("床位数应为正整数！添加失败", category="danger")
            return redirect(url_for("new_room", dorm_id=dorm_id))
        try:
            room = Room(
                id=form.id.data,
                dorm_id=dorm_id,
                level=form.level.data,
                spaces=int(form.spaces.data),
            )
            db.session.add(room)
            db.session.commit()
            flash("添加成功！", category="info")
        except:
            db.session.rollback()
            flash("出现错误，添加失败！", category="danger")
        return redirect(url_for("manage"))
    return render_template("new_room.html", form=form)


@app.route("/fix", methods=["GET", "POST"])
@login_required
def fix():
    if current_user.__class__ == Student:
        return redirect(url_for("index"))
    page = request.args.get("page", 1, type=int)
    dorm_id = current_user.dorm_id
    pagination = (
        db.session.query(Fix)
        .join(Room)
        .filter(Room.dorm_id == dorm_id)
        .paginate(page=page, per_page=5)
    )
    fixes = []
    for fix in pagination.items:
        fixes.append(
            {
                "id": fix.id,
                "student_id": fix.student_id,
                "room_id": fix.room_id,
                "category": fix.category,
                "content": fix.content,
                "submit_time": fix.submit_time,
                "status": fix.status,
            }
        )
    title = [
        ("id", "报修编号"),
        ("student_id", "学号"),
        ("room_id", "房间号"),
        ("category", "类别"),
        ("content", "内容"),
        ("submit_time", "提交时间"),
        ("status", "状态"),
    ]

    return render_template(
        "fixes.html", dorm_id=dorm_id, fix=fixes, title=title, pagination=pagination
    )


class FixInfoForm(FlaskForm):
    submit = SubmitField("已处理")


@app.route("/fix/<int:fix_id>", methods=["GET", "POST"])
@login_required
def fix_info(fix_id):
    fix = Fix.query.get_or_404(fix_id)
    student = Student.query.get(fix.student_id)
    if (
        current_user.__class__ == Manager
        and student.room.dorm_id != current_user.dorm_id
    ):
        return redirect(url_for("index"))
    if current_user.__class__ == Student and student.id != current_user.id:
        return redirect(url_for("index"))
    if fix.status == "未处理":
        form = FixInfoForm()
        if form.validate_on_submit():
            try:
                fix.status = "已处理"
                db.session.commit()
                flash("已处理！", category="info")
            except:
                db.session.rollback()
                flash("出现错误，处理失败！", category="danger")
            return redirect(url_for("fix_info", fix_id=fix_id))
        return render_template("fix_info.html", fix=fix, student=student, form=form)
    return render_template("fix_info.html", fix=fix, student=student)
