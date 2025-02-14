import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ 直接在代码中输入账号和密码
USERNAME = "这里输入帐号，例如u13002xxx"
PASSWORD = "这里输入mis密码"

# ✅ 目标课程信息
TARGET_COURSE_NAME = "German II"  # 课程名称
TARGET_COURSE_ID = "2c9070d994eed9d40194f8d524fc31c2"  # 课程 ID
# TARGET_COURSE_NAME = "Financial Mathematics"  # 课程名称
# TARGET_COURSE_ID = "2c9070d994eed9d40194f8d5266935da"  # 课程 ID

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
        # **查找用户名、密码输入框**
        username_input = driver.find_element(By.ID, "j_username")
        password_input = driver.find_element(By.NAME, "j_password")
        student_radio = driver.find_element(By.ID, "student")
        login_button = driver.find_element(By.XPATH, "//input[@type='image']")

        # **输入账号密码**
        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        # **选择“学生”身份，点击登录**
        student_radio.click()
        login_button.click()

        print("✅ 登录成功！")
        time.sleep(1)  # 等待页面跳转
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        driver.quit()
        exit()
    driver.get("https://mis.uic.edu.cn/mis/student/as/home.do")
    time.sleep(2)


def check_course_status(course_name, course_id):
    """在搜索框中输入课程名称，点击搜索，并检查课程状态"""
    try:
        print(f"🔍 正在搜索课程: {course_name} ...")

        # 1️⃣ 定位搜索框，输入课程名称
        search_box = driver.find_element(By.ID, "keyWord")
        search_box.clear()
        search_box.send_keys(course_name)

        # 2️⃣ 选择 "Search By Course"
        search_type = driver.find_element(By.ID, "keyWordType")
        search_type.send_keys("1")  # 选项 1 = 按课程名称搜索

        # 3️⃣ 点击搜索按钮
        search_button = driver.find_element(By.XPATH, "//button[text()='Search']")
        search_button.click()

        # 4️⃣ 等待搜索结果加载
        time.sleep(3)

        print(f"✅ 课程 {course_name} 搜索完成，检查状态...")

        # 5️⃣ 查找课程 ID 以获取状态
        try:
            course_element = driver.find_element(By.ID, course_id)
        except:
            print(f"❌ 未找到课程 ID {course_id}，可能是搜索结果错误")
            return None

        parent_row = course_element.find_element(By.XPATH, "./parent::tr")

        # 6️⃣ 获取状态按钮
        status_button = parent_row.find_element(By.XPATH, "./td[last()]//input")
        status_text = status_button.get_attribute("value")

        if "Time Clash" in status_text:
            print("⚠️ 课程存在时间冲突，退出抢课循环。")
            return "time_clash"

        if "Full" in status_text:
            print("⏳ 课程已满，进入循环监控...")
            return "full"

        print("✅ 课程可选，尝试抢课！")
        return "available"

    except Exception as e:
        print(f"❌ 检查课程状态失败: {e}")
        return None


import smtplib
import getpass  # 用于手动输入密码
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email():
    """发送抢课成功通知邮件"""
    sender_email = ""
    receiver_email = ""

    # **手动输入密码**
    password = ""

    subject = "✅ 抢课成功通知"
    body = f"""
    亲爱的 Honleun，

    你的课程已经成功抢到！🎉

    课程名称: {TARGET_COURSE_NAME}
    课程 ID: {TARGET_COURSE_ID}

    如果有问题，请检查 UIC MIS 选课系统。

    祝好！
    """

    # **设置邮件内容**
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # **连接 Outlook SMTP 服务器**
        server = smtplib.SMTP("smtp-mail.outlook.com", 587)
        server.starttls()  # **启用 TLS**
        server.login(sender_email, password)  # **手动输入密码**
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()

        print("📧 抢课成功通知已发送！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


def add_course(course_id):
    """尝试添加课程"""
    try:
        print(f"🚀 正在抢课: {course_id}...")

        # **尝试重新获取课程行**
        course_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, course_id))
        )

        # **查找 "Add" 按钮**
        add_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//td[@id='{course_id}']/following-sibling::td//input[@value='Add']"))
        )

        # **点击 "Add" 按钮**
        add_button.click()

        # **处理弹窗确认**
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()  # 点击“确定”

        print(f"🎉 成功抢到课程: {course_element.text}")

        # **发送邮件通知**
        # send_email()

        return True

    except Exception as e:
        if "stale element reference" in str(e):
            print("✅ 课程抢到了！尽管发生 stale element reference 错误，但可以视为成功。")
            # send_email()  # **仍然发送邮件**
            return True
        else:
            print(f"❌ 抢课失败: {e}")
            return False

def monitor_course(course_name, course_id):
    """如果课程已满，进入循环监控"""
    while True:
        print("🔄 重新搜索课程...")
        driver.refresh()
        time.sleep(random.uniform(5, 10))  # **随机间隔时间，减少封锁风险**

        status = check_course_status(course_name, course_id)

        if status == "available":
            add_course(course_id)
            break
        elif status == "time_clash":
            print("🚫 课程时间冲突，终止监控。")
            break
        elif status == "full":
            print("⏳ 课程仍然已满，继续监控...")
        else:
            print("⚠️ 未知状态，重新尝试...")


# **执行抢课流程**
login()
status = check_course_status(TARGET_COURSE_NAME, TARGET_COURSE_ID)

if status == "available":
    add_course(TARGET_COURSE_ID)
elif status == "full":
    monitor_course(TARGET_COURSE_NAME, TARGET_COURSE_ID)
elif status == "time_clash":
    print("❌ 课程时间冲突，退出脚本。")
else:
    print("❌ 课程状态未知，检查是否有错误。")

# **结束 WebDriver 进程**
driver.quit()