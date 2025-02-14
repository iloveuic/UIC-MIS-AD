import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ 账号和密码（直接写在代码中）
USERNAME = "这里输入mis帐号"
PASSWORD = "这里输入mis密码"

# ✅ 目标课程列表（名称与 ID 一一对应）
# 可以根据需要添加更多课程
COURSES = [
    {"name": "German II", "id": "2c9070d994eed9d40194f8d524fc31c2"},
    {"name": "Technology and Innovation Strategy (1002)", "id": "2c9070d994eed9d40194f8d525fa344e"},
]

# ✅ ChromeDriver 路径
CHROME_DRIVER_PATH = "chromedriver/chromedriver"
service = Service(CHROME_DRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # 最大化窗口
driver = webdriver.Chrome(service=service, options=options)


def login():
    """自动登录 UIC MIS 选课系统"""
    print("🔑 正在打开 UIC MIS 登录页面...")
    driver.get("https://mis.uic.edu.cn/mis/student/as/home.do")
    time.sleep(1)

    try:
        # 定位用户名、密码输入框
        username_input = driver.find_element(By.ID, "j_username")
        password_input = driver.find_element(By.NAME, "j_password")
        student_radio = driver.find_element(By.ID, "student")
        login_button = driver.find_element(By.XPATH, "//input[@type='image']")

        # 输入账号密码
        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        # 选择“学生”身份，点击登录
        student_radio.click()
        login_button.click()

        print("✅ 登录成功！")
        time.sleep(1)  # 等待页面跳转
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        driver.quit()
        exit()

    # 登录后再次跳转到首页
    driver.get("https://mis.uic.edu.cn/mis/student/as/home.do")
    time.sleep(2)


def check_course_status(course_name, course_id):
    """
    在搜索框中输入课程名称，点击搜索，并检查课程状态
    返回值:
        "available"  可选（尝试抢课）
        "full"       已满
        "time_clash" 时间冲突
        None         出错或未知状态
    """
    try:
        print(f"🔍 正在搜索课程: {course_name} ...")
        # 定位搜索框，输入课程名称
        search_box = driver.find_element(By.ID, "keyWord")
        search_box.clear()
        search_box.send_keys(course_name)

        # 选择 "Search By Course"（选项 1 = 按课程名称搜索）
        search_type = driver.find_element(By.ID, "keyWordType")
        search_type.send_keys("1")

        # 点击搜索按钮
        search_button = driver.find_element(By.XPATH, "//button[text()='Search']")
        search_button.click()

        # 等待搜索结果加载
        time.sleep(3)
        print(f"✅ 课程 {course_name} 搜索完成，检查状态...")

        # 根据课程 ID 定位课程元素
        try:
            course_element = driver.find_element(By.ID, course_id)
        except Exception as e:
            print(f"❌ 未找到课程 ID {course_id}，可能是搜索结果错误")
            return None

        parent_row = course_element.find_element(By.XPATH, "./parent::tr")

        # 获取状态按钮并读取按钮文本
        status_button = parent_row.find_element(By.XPATH, "./td[last()]//input")
        status_text = status_button.get_attribute("value")

        if "Time Clash" in status_text:
            print(f"⚠️ 课程 {course_name} 存在时间冲突。")
            return "time_clash"

        if "Full" in status_text:
            print(f"⏳ 课程 {course_name} 已满，继续监控...")
            return "full"

        print(f"✅ 课程 {course_name} 可选，尝试抢课！")
        return "available"

    except Exception as e:
        print(f"❌ 检查课程状态失败: {e}")
        return None


def send_email(course):
    """发送抢课成功通知邮件（此处仅作示例，需确保 SMTP 相关设置正确）"""
    sender_email = ""
    receiver_email = ""
    password = ""  # SMTP 授权码或密码

    subject = "✅ 抢课成功通知"
    body = f"""
    亲爱的 Honleun，

    你的课程已经成功抢到！🎉

    课程名称: {course['name']}
    课程 ID: {course['id']}

    如果有问题，请检查 UIC MIS 选课系统。

    祝好！
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp-mail.outlook.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("📧 抢课成功通知邮件已发送！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


def add_course(course_id):
    """尝试添加课程"""
    try:
        print(f"🚀 正在抢课: {course_id} ...")

        # 等待课程行加载
        course_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, course_id))
        )

        # 定位 “Add” 按钮
        add_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//td[@id='{course_id}']/following-sibling::td//input[@value='Add']"))
        )

        # 点击 “Add” 按钮
        add_button.click()

        # 处理弹窗确认
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()  # 点击“确定”

        print(f"🎉 成功抢到课程: {course_element.text}")
        # 如有需要，可发送邮件通知
        # send_email(course)

        return True

    except Exception as e:
        if "stale element reference" in str(e):
            print("✅ 课程抢到了！尽管发生 stale element reference 错误，但可以视为成功。")
            # send_email(course)  # 如有需要，可发送邮件
            return True
        else:
            print(f"❌ 抢课失败: {e}")
            return False


def monitor_courses(courses):
    """
    监控多个目标课程，
    对每个课程：每次刷新页面、搜索课程，间隔 5-10 秒
    如果某门课程抢到或遇到时间冲突则停止监控该课程，
    当所有课程都处理完毕后退出监控循环。
    """
    # 将未成功抢到的课程存入监控列表
    remaining_courses = courses.copy()

    while remaining_courses:
        # 遍历当前需要监控的课程（使用副本以便在循环内删除已处理课程）
        for course in remaining_courses.copy():
            print(f"\n========== 开始监控课程：{course['name']} ==========")
            # 每次操作前刷新页面
            driver.refresh()
            # 随机等待 5-10 秒
            delay = random.uniform(5, 10)
            print(f"等待 {delay:.1f} 秒后进行搜索...")
            time.sleep(delay)

            status = check_course_status(course["name"], course["id"])

            if status == "available":
                if add_course(course["id"]):
                    print(f"🎉 课程 {course['name']} 已抢到，停止监控该课程。")
                    remaining_courses.remove(course)
                    # 如需要，每次抢到后可发送邮件通知
                    # send_email(course)
            elif status == "time_clash":
                print(f"🚫 课程 {course['name']} 存在时间冲突，停止监控该课程。")
                remaining_courses.remove(course)
            elif status == "full":
                print(f"⏳ 课程 {course['name']} 依然已满，稍后继续监控。")
            else:
                print(f"⚠️ 课程 {course['name']} 状态未知，将重新尝试。")

            # 如果所有课程都处理完毕，则退出外层循环
            if not remaining_courses:
                break

    print("\n✅ 所有目标课程均已处理，退出监控。")


# 执行流程
login()
monitor_courses(COURSES)

# 结束 WebDriver 进程
driver.quit()