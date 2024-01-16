# encoding: utf-8
import os
import re
import sys
import glob
import time
import json
import tqdm
import random
import numpy as np
import shutil
import logging
from datetime import datetime
from selenium import webdriver
from screeninfo import get_monitorss
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def print_verbose(message, verbose=True):
    if verbose:
        print(message)


def validate_and_create_path(path, verbose=True):
    """
    验证给定的路径格式并确保其存在。

    参数:
    - path: 需要检查和创建的路径
    - verbose: 是否打印提示信息，默认为True

    返回:
    - bool: 路径格式是否正确以及路径是否成功创建或已存在
    """

    # 验证路径格式
    if os.name == 'posix' and not path.startswith('/'):
        print_verbose(f"错误：对于 macOS/Linux 系统，路径 '{path}' 应以 '/' 开头。")
        sys.exit(1)
    elif os.name == 'nt' and (len(path) < 2 or path[1] != ':'):
        print_verbose(f"错误：对于 Windows 系统，路径 '{path}' 的第二个字符应为 ':'。")
        sys.exit(1)

    # 检查路径是否存在
    if not os.path.exists(path):
        print_verbose(f"提示：路径 '{path}' 不存在，尝试创建...")
        try:
            os.makedirs(path)
            if verbose:
                print(f"提示：路径 '{path}' 成功创建！")
        except Exception as e:
            if verbose:
                print(f"错误：创建路径 '{path}' 时出现异常，原因：{e}")
    else:
        print_verbose(f"提示：路径 '{path}' 校验通过。")


def verify_element_value(driver, xpath, expected_value, return_bool=False, verbose=True):
    """
    通过给定的 XPath 定位到元素并获取其值，然后与期望的值进行比较。

    参数:
    - driver: WebDriver 实例。
    - xpath: 用于定位元素的 XPath 字符串。
    - expected_value: 期望的值，可以是字符串或数字。
    - return_bool: 是否返回布尔值。如果为 False 并且值不匹配，将会抛出异常。
    - verbose: 是否在关键步骤打印详细信息，默认为True。

    返回:
    - bool: 如果元素的值与期望的值匹配返回 True，否则返回 False，并抛出错误。
    """

    # 定位元素
    try:
        element = driver.find_element(By.XPATH, xpath)
        print_verbose("提示：成功定位到元素。")
    except Exception as e:
        print_verbose(f"错误：定位元素失败，原因：{e}")
        return False

    # 获取元素的值
    element_value = element.get_attribute("value")
    if element_value is None:
        element_value = element.text
    print_verbose(f"提示：待验证元素值为：{element_value}")

    # 将值转为字符串进行比较
    if isinstance(expected_value, (int, float)):
        expected_value = str(expected_value)
    if isinstance(element_value, (int, float)):
        element_value = str(element_value)

    if element_value == expected_value:
        print_verbose("提示：待验证元素与预期值匹配。")
        if return_bool:
            return True
    else:
        if return_bool:
            return False
        raise ValueError(f"待验证元素值 {element_value} 与预期值 {expected_value} 不符合。")


def get_power_law_pause(min_pause=1.618, max_pause=5.42, exponent=0.2):
    """
    根据幂律分布生成一个随机的停留时间。

    参数:
    - exponent: 幂律分布的指数。
    - min_pause: 生成的停留时间的最小值。
    - max_pause: 生成的停留时间的最大值。

    返回:
    - 一个随机的停留时间，它的值在 [min_pause, max_pause] 范围内。
    """
    random_value = np.random.power(exponent)
    return min_pause + (max_pause - min_pause) * random_value


def random_delay(min_sec=1.8, max_sec=5.42, verbose=True):
    """
    根据给定的最小和最大秒数范围，使用 power law 分布计算随机的暂停时间并使线程暂停。

    参数:
    - min_sec: 随机暂停的最小秒数。默认为 1.8 秒。
    - max_sec: 随机暂停的最大秒数。默认为 5.42 秒。

    返回:
    None. 该函数会使当前线程暂停。
    """

    sleep_time = get_power_law_pause(min_pause=min_sec, max_pause=max_sec)
    time.sleep(sleep_time)
    if verbose:
        print(f"提示：按幂律分布装睡 {sleep_time:.2f} 秒.")


def is_domain_present(driver, domain, timeout=20, check_interval=5, verbose=True):
    """
    检查当前浏览器的句柄是否包含指定的域名。

    参数:
    - driver: webdriver 实例
    - domain: 要检查的域名
    - timeout: 检测超时时长
    - check_interval: 每次检查之间等待的时间
    - verbose: 是否打印详细信息

    返回值:
    如果找到域名则返回 True, 否则返回 False。
    """

    print_verbose(
        f"提示：正在以 {check_interval} 秒一次的频率，检查 {domain} 是否出现在浏览器 Tab...")

    # 优先检查当前 tab
    if domain in driver.current_url:
        print_verbose(f"提示：URL {domain} 已出现在当前 Tab！")
        return True

    end_time = time.time() + timeout
    check_count = 0
    current_handle = driver.current_window_handle

    while time.time() < end_time:
        check_count += 1
        # 检查其他tabs
        for handle in driver.window_handles:
            if handle == current_handle:
                continue  # Skip current tab as we already checked it
            driver.switch_to.window(handle)
            if domain in driver.current_url:
                print_verbose(f"提示：URL {domain} 已出现在其他 Tab！")
                return True

        print_verbose(f"提示：第 {check_count} 次检查未发现 {domain}。")
        time.sleep(check_interval)

    print_verbose(f"提示：经历 {check_count} 次检查后还是没检查到 {domain}。")
    return False


def random_scroll_partial(driver, direction_choice=['up', 'down'], arrows=4, delay_between_scrolls=True):
    """
    使用给定的webdriver对象执行部分滚动。

    参数:
    - driver: 用于滚动的webdriver对象。
    - direction_choice: 可选的滚动方向列表，默认为['up', 'down']。
    - arrows: 按箭头键的次数来决定滚动的大小，默认为5。
    - delay_between_scrolls: 每次滚动之间是否执行随机休眠，默认为True。

    返回:
    None
    """

    # 确定滚动方向（向上或向下）
    chosen_direction = random.choice(direction_choice)
    if chosen_direction == 'up':
        key_to_press = Keys.ARROW_UP
    elif chosen_direction == 'down':
        key_to_press = Keys.ARROW_DOWN
    else:
        raise ValueError("Invalid direction choice. Must be 'up' or 'down'.")

    # 执行滚动操作
    body = driver.find_element(By.XPATH, '//body')
    for _ in range(arrows):
        body.send_keys(key_to_press)
        if delay_between_scrolls:
            random_delay(min_sec=0.5, max_sec=2.42)


def human_type(input_element, text):
    """
    模拟人类输入速度.

    参数:
    - input_element: 要输入文本的 Selenium WebElement。
    - text: 要输入的文本。
    """
    for char in text:
        input_element.send_keys(char)
        random_delay(0.5, 1.5)  # 使用默认的延迟范围


def create_chrome_driver(chrome_user_data_path, download_path):
    """
    创建并返回一个配置过的 Chrome WebDriver 实例。

    参数:
    - chrome_user_data_path: 持久化用户数据文件夹路径
    - download_path: 默认下载文件夹路径

    返回:
    - driver: 配置好的 WebDriver 实例
    """
    try:
        print(f"提示：正在配置用户数据目录为: {chrome_user_data_path}")

        # 使用 uc.ChromeOptions 替代原生的 webdriver.ChromeOptions
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={chrome_user_data_path}")

        print(f"提示：正在配置默认下载目录为: {download_path}")
        options.add_experimental_option(
            'prefs', {'download.default_directory': download_path})

        print("提示：正在初始化 Chrome WebDriver 实例...")

        # 使用 uc.Chrome 替代原生的 webdriver.Chrome
        driver = uc.Chrome(options=options)
        print("提示：WebDriver 实例创建成功。")

        return driver
    except Exception as e:
        print(f"错误：创建 WebDriver 实例时发生错误：{e}")


def is_sunshine_logged_in(driver):
    """检查是否成功登录日光图书馆"""
    try:
        welcome_elem = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'login-title') and contains(., '欢迎您')]"))
        )
        print("提示：日光图书馆登录成功。")
        return True
    except TimeoutException:
        return False


def switch_tab_by_domain(driver, domain_type="sunshine"):
    """
    根据指定的域名类型切换到相应的tab。

    参数:
    - driver: WebDriver 实例。
    - domain_type: 切换目的域名类型，默认为 'sunshine'。

    返回:
    - bool: 如果成功切换，返回 True，否则抛出异常。
    """

    domain_patterns = {
        "sunshine": (r"www\.99885\.net", "http://www.99885.net/"),
        "wos": (r"www\.webofscience\.com", "https://www.webofscience.com/wos/woscc/basic-search")
        # 可以在此处为其他的domain_type添加相应的正则模式和重定向URL
    }

    if domain_type not in domain_patterns:
        valid_domain_types = ", ".join(domain_patterns.keys())
        raise ValueError(
            f"错误：'{domain_type}' 不是一个有效的域名类型。当前有效的域名类型有: {valid_domain_types}")

    url_pattern, redirect_url = domain_patterns[domain_type]

    handles = driver.window_handles
    for handle in handles:
        driver.switch_to.window(handle)
        if re.search(url_pattern, driver.current_url):
            # 如果URL不等于指定的redirect_url，则跳转到指定的redirect_url
            if driver.current_url != redirect_url:
                driver.get(redirect_url)
            print(f"提示：已成功切换至 {driver.title} {driver.current_url}。")
            return True


def hover_pause_click(driver, xpath_locator, click_after_hover=True, min_pause=1.42, max_pause=5.42, timeout=7.618, exponent=0.2, retry_attempts=0, hover_ratio=0.5):
    """
    使用 ActionChains 在给定的 xpath_locator 上悬浮、随机停顿、并根据需要点击元素。

    参数:
    - driver: WebDriver 实例。
    - xpath_locator: 要悬浮和点击的元素的 XPath。
    - click_after_hover: 是否在悬浮和暂停后点击元素。
    - min_pause: 悬浮后的最小停顿时间（秒）。
    - max_pause: 悬浮后的最大停顿时间（秒）。
    - timeout: 等待元素出现最大时间（秒）。
    - exponent: 幂律分布的指数。
    - retry_attempts: 操作失败时的重试次数。
    - hover_ratio: 控制偏移自元素中心的比例。
    """

    for attempt in range(retry_attempts + 1):  # 加 1 是为了确保至少执行一次
        try:
            # 首先定位到元素
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath_locator))
            )

            # 获取元素的大小以确定随机位置
            random_x_offset = (element.size["width"] / 2) * hover_ratio
            random_y_offset = (element.size["height"] / 2) * hover_ratio

            # 使用 ActionChains 执行悬停到随机位置、暂停和（如果需要的话）点击操作
            pause_duration = get_power_law_pause(
                min_pause, max_pause, exponent)

            actions = ActionChains(driver)
            actions.move_to_element(element).move_by_offset(
                random_x_offset, random_y_offset)
            actions.pause(pause_duration)

            if click_after_hover:
                actions.click()

            actions.perform()
            return  # 操作成功，退出函数

        except Exception as e:
            if attempt < retry_attempts:  # 如果不是最后一次尝试，继续
                wos_close_pendo(driver)  # 这个函数似乎是一个自定义函数，确保你的代码中包含了它
                continue
            else:
                raise Exception(
                    f"经过 {retry_attempts + 1} 次尝试元素悬停点击, 错误发生在： '{xpath_locator}': {e}")


def initiate_sunshine_login(driver, username, password):
    """日光图书馆的登录流程"""
    print('提示：开始模拟登录日光图书馆...')
    username_elem = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "user_name"))
    )
    password_elem = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "password"))
    )

    random_delay(2, 4)
    print('提示：模拟登陆需要模拟手动输入，请耐心等待~')
    human_type(username_elem, username)
    human_type(password_elem, password)
    print('提示：请手动输入验证码并点击登录按钮！')

    try:
        welcome_elem = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'login-title') and contains(., '欢迎您')]"))
        )
        print("提示：日光图书馆全新登录成功。")
    except TimeoutException:
        print("提示：日光图书馆全新登录失败。")


def login_to_channel(channel, username, password, user_data_path=None,
                     wos_download_path=None, window_percentage=90, verbose=False):
    """
    登录到指定 WoS 权限通道网站。

    参数:
    - channel: 登录的来源或平台 (例如日光图书馆："sunshine")
    - username: 登录的用户名
    - password: 登录的密码
    - user_data_path: 用户数据文件夹路径
    - window_percentage: 实例窗口大小占显示器大小的百分比，范围从 1 到 100。默认为 80%。

    返回:
    - driver: 登录尝试后的WebDriver实例
    """

    # 根据不同的 channel 定义对应的 url
    urls = {
        "sunshine": "http://www.99885.net"
        # 这里可以添加其他 channels 和其对应的 urls
    }

    print_verbose(message="提示：正在验证 channel 类型...", verbose=verbose)
    if channel not in urls:
        print(f"错误：未定义的 channel: {channel}。")
        return None

    # 使用之前的函数初始化 driver
    print_verbose(message="提示：初始化 Chrome WebDriver...", verbose=verbose)
    driver = create_chrome_driver(user_data_path, wos_download_path)
    set_browser_to_percentage_of_screen(
        driver=driver, percentage=window_percentage, verbose=verbose)
    driver.get(urls[channel])

    # 验证是否成功登录
    print_verbose(message="提示：正在验证登录状态...", verbose=verbose)
    if channel == "sunshine":
        if not is_sunshine_logged_in(driver):
            print("提示：用户未登录，现在登录。")
            initiate_sunshine_login(driver, username, password)

    # TODO: 其他来源
    return driver


def is_new_tab_opened(driver, timeout):
    """
    检查在指定的最大时间内，是否有新的Tab被打开。

    参数:
        driver (webdriver instance): 已经打开的浏览器实例。
        timeout (int): 检查的最大等待时间（秒）。

    返回:
        bool: 如果新的Tab在指定的时间内打开，则返回True，否则返回False。
    """
    initial_tabs = len(driver.window_handles)
    try:
        # 使用WebDriverWait，等待新的Tab被打开
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.window_handles) > initial_tabs
        )
        return True
    except TimeoutException:
        return False


def goto_wos_captcha(driver, timeout=42, max_retries=3):
    """
    导航到 WoS 的验证码页面，如果成功登陆日光图书馆，则在浏览器界面进行相应提示。

    参数:
    - driver: WebDriver 实例。
    - timeout: 等待元素出现的最大时限（秒）。默认为 30 秒。
    - max_retries: 重试的最大次数，默认为 3。

    返回:
    None. 函数主要进行导航和交互操作。
    """

    retries = 0
    while retries < max_retries:
        try:
            # 判断当前 Tab 是否在 http://www.99885.net/
            if driver.current_url != "http://www.99885.net/":
                driver.get("http://www.99885.net")

            # 等待登陆成功的标志元素出现
            login_success_elem = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'login-title') and contains(., '欢迎您')]"))
            )
            print(f"提示：现在跳转至 Wos...当人机验证页面弹出后，请在 {timeout} 秒内手动完成验证。")

            # 使用 hover_pause_click 函数进行操作
            hover_pause_click(
                driver, "//a[@class='h-m-n-link' and text()='资源列表']", min_pause=2, click_after_hover=False)
            hover_pause_click(
                driver, "//a[@rel='nofollow' and @class='h-s-n-link' and text()='英文数据库']")
            hover_pause_click(driver, "//a[text()=' Web of Science']")

            if is_domain_present(driver=driver, domain="webofscience.com", timeout=timeout-5):
                print("提示：请检查是否跳转成功。")
                return

        except TimeoutException:
            # 处理登陆失败
            retries += 1
            if retries >= max_retries:
                if not login_success_elem:
                    print("提示：未登陆日光图书馆，请重复登陆步骤")
                else:
                    print("提示：时限内未完成跳转，现跳转回首页，请重试人机验证。")
                driver.get("http://www.99885.net")
                break


def wos_close_pendo(driver):
    '''关闭悬浮窗口'''
    elements_to_click = [
        "//button[contains(@class, 'onetrust-close-btn-handler') and @aria-label='关闭']",
        '//button[contains(@class, "_pendo-button-primaryButton")]',
        '//button[contains(@class, "_pendo-button-secondaryButton")]',
        '//span[contains(@class, "_pendo-close-guide")]',
        '//*[@id="pendo-close-guide-a5a67841"]',
        '//*[@id="pendo-close-guide-5600f670"]',
        "//mat-icon[contains(@class, 'material-icons') and contains(text(), 'close')]"
    ]

    closed_count = 0  # 记录成功关闭的元素数量

    for xpath in elements_to_click:
        try:
            element = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            actions = ActionChains(driver)
            actions.move_to_element(element).pause(get_power_law_pause(
                min_pause=1.618, max_pause=2.42)).click(element).perform()
            closed_count += 1  # 成功关闭元素后递增计数
            print(f"尊敬的大人，罪犯元素：{xpath} 已被枪决！")
        except Exception:  # 捕获所有异常，因为不仅仅是元素不存在的问题
            pass

    # 根据关闭元素的数量返回 True 或 False
    return closed_count > 0


def wos_detective_inspector(driver):
    # 定义元素定位器
    need_to_close_element_locator = (
        By.XPATH, '//h2[contains(text(), "Continue on to claim your record")]')
    close_button_locator = (By.CSS_SELECTOR, 'mat-icon.material-icons')

    try:
        # 检查指定的元素是否存在
        h2_element = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located(need_to_close_element_locator)
        )

        # 如果找到该元素，则找到 close 按钮并悬浮到它
        close_button_element = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located(close_button_locator)
        )

        hover_action = ActionChains(
            driver).move_to_element(close_button_element)
        hover_action.perform()

        # 调用关闭函数
        wos_close_pendo()

        return True  # 表示成功找到并处理元素

    except:
        return False  # 表示元素不存在


def wos_switch_english(driver, retries=3):

    if not is_domain_present(driver=driver, domain="webofscience.com", check_interval=2, timeout=10):
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if "webofscience.com" in driver.current_url:
                break

    for _ in range(retries):
        try:
            random_delay(1, 3)  # 强制随机装死

            chinese_button = driver.find_element(
                By.XPATH, '//*[normalize-space(text())="简体中文"]')
            # 模拟鼠标移动到元素
            ActionChains(driver).move_to_element(chinese_button).perform()
            random_delay(0.5, 1.5)  # 模拟人的反应时间
            chinese_button.click()

            # 等待并点击英文按钮
            english_button = driver.find_element(
                By.XPATH, '//button[@lang="en"]')
            ActionChains(driver).move_to_element(english_button).perform()
            random_delay(0.5, 1.5)
            english_button.click()

            return

        except Exception as e:
            print(f"错误：{e}，重试...")
            continue

    print(f"经过 {retries} 次尝试后，切换为英语仍然失败.")


def wos_goto_advanced_search(driver, method="click", timeout=20, verbose=True):
    """
    根据所选择的方法导航至 Advanced Search 页面。

    参数:
    - driver: WebDriver 实例。
    - method: 指定导航方法，可为 "click" 或 "direct_access"。
    - timeout: 点击方式，等待元素最大时间（秒）。
    - verbose: 控制是否打印提示信息。
    """

    attempts = 3

    if method == "click":
        for i in range(attempts):
            try:
                # 等待页面加载并找到高级查询的链接
                advanced_search_element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//a[@data-ta="advanced-search-link"]'))
                )
                print_verbose("提示：找到高级查询链接")

                # 使用 ActionChains 进行点击操作
                actions = ActionChains(driver)
                actions.move_to_element(advanced_search_element).pause(get_power_law_pause(
                    min_pause=1.618, max_pause=2.42)).click(advanced_search_element).perform()
                print_verbose("提示：成功点击高级查询链接")
                # 如果点击成功，跳出循环
                break
            except Exception as e:
                if i < attempts - 1:  # 如果不是最后一次尝试，就继续
                    print_verbose(f"提示：点击尝试 {i + 1} 次失败，重试中...")
                    continue
                else:  # 如果是最后一次尝试并且仍然失败，就抛出异常
                    raise Exception(f"提示：点击尝试 {attempts} 次后失败。错误信息: {e}")

    elif method == "direct_access":
        for i in range(attempts):
            try:
                url = "https://www.webofscience.com/wos/woscc/advanced-search"
                driver.get(url)
                print_verbose("提示：成功直接访问高级查询页面")
                # 如果上面的操作成功，则跳出循环
                break
            except Exception as e:
                if i < attempts - 1:  # 如果不是最后一次尝试，就继续
                    print_verbose(f"提示：直接访问尝试 {i + 1} 次失败，重试中...")
                    continue
                else:  # 如果是最后一次尝试并且仍然失败，就抛出异常
                    raise Exception(f"提示：直接访问尝试 {attempts} 次后失败。错误信息: {e}")

    else:
        print(f"错误: {method}。请选择 'click' 或 'direct_access'。")


def wos_advanced_search(driver, query, verbose=True):
    """
    执行高级搜索操作：清除搜索框、插入查询词并点击搜索按钮。

    参数:
    - driver: Selenium 的 WebDriver 实例。
    - query: 需要搜索的查询表达式字符串。
    - verbose: 是否打印提示。
    """

    attempts = 3
    for i in range(attempts):
        try:
            print_verbose("提示：等待清除按钮出现...")
            clear_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//span[contains(@class, "mat-button-wrapper") and text()=" Clear "]'))
            )

            print_verbose("提示：点击清除按钮...")
            actions_clear = ActionChains(driver)
            actions_clear.move_to_element(clear_button).pause(get_power_law_pause(
                min_pause=1.618, max_pause=2.42)).click(clear_button).perform()

            print_verbose("提示：插入查询表达式...")
            input_element = driver.find_element(
                By.XPATH, '//*[@id="advancedSearchInputArea"]')
            input_element.send_keys(query)

            print_verbose("提示：点击搜索按钮...")
            search_button = driver.find_element(
                By.XPATH, '//span[contains(@class, "mat-button-wrapper") and text()=" Search "]')
            actions_search = ActionChains(driver)
            actions_search.move_to_element(search_button).pause(get_power_law_pause(
                min_pause=1.618, max_pause=2.42)).click(search_button).perform()

            print_verbose("提示：等待查询页面加载...")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'title-link'))
            )
            print_verbose("提示：查询页面已加载完成。")

            # 如果所有操作都成功，则跳出循环
            break
        except Exception as e:
            if i < attempts - 1:  # 如果不是最后一次尝试，就继续
                if verbose:
                    print(f"提示：操作失败，尝试第 {i+2} 次...")
                random_delay()
                continue
            else:  # 如果是最后一次尝试并且仍然失败，就抛出异常
                raise Exception(f"错误：尝试 {attempts} 次后失败，错误信息: {e}")


def wos_query_result_arrange(driver):
    """
    对搜索结果按从旧到新排序，以实现增量下载。

    参数:
    - driver: Selenium 的 WebDriver 实例。
    """
    # 定位到“Sort by”元素并悬浮点击
    sort_by_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//span[contains(@class, "label colonMark") and text()="Sort by"]'))
    )

    actions_sort_by = ActionChains(driver)
    actions_sort_by.move_to_element(sort_by_element).pause(get_power_law_pause(
        min_pause=1.618, max_pause=2.42)).click(sort_by_element).perform()

    # 在浮层中定位到“Date: newest first”按钮并悬浮点击
    date_descending_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="date-ascending"]'))
    )

    actions_date_descending = ActionChains(driver)
    actions_date_descending.move_to_element(date_descending_element).pause(get_power_law_pause(
        min_pause=1.618, max_pause=2.42)).click(date_descending_element).perform()


def wos_query_result_count(driver):
    """
    从 Web of Science 的查询结果页面中提取查询结果的记录数。

    参数:
    - driver: WebDriver 实例。

    返回:
    - results_count: 从页面中提取并转换为整数的查询结果总数。
    """

    try:
        # 定位到含有查询结果总数的元素
        element = driver.find_element(
            By.XPATH, '//h1[@class="search-info-title font-size-20 ng-star-inserted"]/span[@class="brand-blue"]')

        # 从元素的文本中提取数字并转换为整数
        results_count = int(element.text.replace(',', ''))
        return results_count
    except Exception as e:
        print(f"Error encountered while extracting the result count: {e}")
        return None


def wos_get_download_ranges(driver, start=1, end=None):
    """
    根据给定的查询结果和用户指定的起止点，计算并返回每个下载任务的起始和结束范围。

    参数:
    - driver: WebDriver 实例。
    - start: 用户指定的下载起始点，默认为 1。
    - end: 用户指定的下载结束点。如果没有指定，将使用查询结果的总记录数；如果指定的结束点超过查询结果的总记录数，会自动调整。

    返回:
    - download_ranges: 一个列表，其中每个元素都是一个元组，表示每个下载任务的起始和结束范围。
    """

    total_count = wos_query_result_count(driver)

    if end is None:
        end = total_count
    elif end > total_count:
        print("提示：你要求导出的记录数超出了查询结果，已为你自动调整。")
        end = total_count

    download_ranges = []
    max_records_per_download = 500

    while start <= end:
        range_end = start + max_records_per_download - 1
        if range_end > end:
            range_end = end
        download_ranges.append((start, range_end))
        start = range_end + 1

    return download_ranges


def scroll_to_top(driver):
    """使用给定的 webdriver 对象滚动到页面顶部。

    参数:
    - driver: webdriver对象

    返回:
    None
    """
    body = driver.find_element_by_tag_name('body')
    body.send_keys(Keys.HOME)


def human_clear(driver, xpath_locator, min_pause=1.68, max_pause=2.89):
    """
    以模拟人类的方式清除给定XPath定位器的输入框内容。

    参数:
    - driver: WebDriver 实例。
    - xpath_locator: 输入框的 XPath。
    - min_pause: 所有操作之间的最小暂停时间（秒）。
    - max_pause: 所有操作之间的最大暂停时间（秒）。
    """

    # 等待元素直到它变得可点击
    wait = WebDriverWait(driver, 15)
    input_element = wait.until(
        EC.element_to_be_clickable((By.XPATH, xpath_locator)))

    # 模拟人类的悬停操作
    actions = ActionChains(driver)
    actions.move_to_element(input_element).pause(
        get_power_law_pause(min_pause, max_pause))

    # 模拟人类的双击操作
    actions.double_click(input_element).perform()

    # 随机暂停
    time.sleep(random.uniform(1.2, 3.14))

    # 删除选择的内容
    actions.send_keys(Keys.DELETE).perform()


def wos_export_dialog_exists(driver, wait_time=45):
    """
    等待指定的秒数（默认为 20 秒），查看"Export Records to Plain Text File"的窗口是否消失。
    如果窗口消失了，返回 True，否则返回 False。
    """
    try:
        WebDriverWait(driver, wait_time).until(
            EC.invisibility_of_element_located(
                (By.XPATH, '//*[text()[contains(string(), "Records from:")]]'))
        )
        return True
    except:
        return False


def save_log(query_content, start_record, end_record, download_task_log_path=".", task_status="", error_msg=None):
    """
    保存日志信息

    参数:
    - query_content: 查询内容。
    - start_record: 起始记录号。
    - end_record: 结束记录号。
    - download_task_log_path: 日志文件保存路径，默认为当前路径。
    - task_status: 任务状态。
    - error_msg: 错误信息。

    返回:
    - None
    """

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = os.path.join(download_task_log_path,
                            f"task_details_{timestamp}.json")
    task_info = {
        "query_content": query_content,
        "start_record": start_record,
        "end_record": end_record,
        "timestamp": timestamp,
        "sort_by": "Date: oldest first",
        "status": task_status
    }
    if error_msg:
        task_info["error_msg"] = error_msg

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(json.dumps(task_info, ensure_ascii=False, indent=4))
    print(
        f"提示：已保存 {task_status} 日志到 {filename}，导出任务: '{query_content}', 记录范围: {start_record}-{end_record}")


def wos_download_bricklayer(driver, query_content, start_record, end_record, download_task_log_path=".", max_retries=7):
    """
    为 Web of Science (WoS) 执行下载任务。尝试最多指定次下载，如果都失败，会记录失败的任务详情。

    参数:
    - driver: WebDriver 实例。
    - query_content: 查询内容，用于下载日志。
    - start_record: 起始记录号。
    - end_record: 结束记录号。
    - download_task_log_path: 任务完成与否会记录到文件，并保存到这个路径，默认为当前路径。

    返回:
    - bool: 如果下载任务成功，返回 True，否则返回 False。
    """

    if is_domain_present(driver=driver, domain="webofscience.com/wos/woscc/summary", verbose=False):
        print("提示：自检通过，当前处于检索结果页面。")
        url_query_result = driver.current_url
    else:
        print("提示：自检失败，当前未处于检索结果页面，现尝试重新执行高级查询...")
        wos_goto_advanced_search(driver=driver, method="direct_access")
        wos_advanced_search(driver=driver, query=query_content)
        random_scroll_partial(driver, ['down'], arrows=9)
        url_query_result = driver.current_url

    for attempt in range(max_retries):
        try:
            if wos_export_dialog_exists(driver=driver, wait_time=3):
                print("提示：导出框对话框不存在，进入新下载流程...")
            else:
                print("提示：导出对话框异常存在，现尝试取消。")
                hover_pause_click(
                    driver, xpath_locator='//span[@class="mat-button-wrapper" and text()=\'Cancel \']', retry_attempts=3)
                print("提示：成功取消导出对话框，进入新下载流程...")

            print(
                f"提示：正在尝试第 {attempt + 1} 次下载搜索结果记录范围: {start_record}～{end_record} ...")

            # 悬停并点击 "Export"
            hover_pause_click(
                driver, '//span[contains(@class, "mat-button-wrapper") and text()=" Export "]')
            print("提示：已点击检索结果页导出按钮")

            if not wos_export_dialog_exists(driver=driver, wait_time=5):
                print("提示：导出框对话框出现，接下来选择到出文件类型...")

            # 悬停并点击 "Plain text file"
            try:
                hover_pause_click(
                    driver, '//button[contains(@class, "mat-menu-item") and text()=" Plain text file "]')
            except:
                hover_pause_click(
                    driver, '//button[contains(@class, "mat-menu-item") and @aria-label="Plain text file"]')
            print("提示：已选择导出为纯文本文件")

            # 悬停并点击 "Records from:"
            hover_pause_click(
                driver=driver, xpath_locator='//*[text()[contains(string(), "Records from:")]]', hover_ratio=0.05)
            print("提示：已点击记录范围选择")

            # 清空并输入起始记录号
            start_record_input_xpath = '//input[@name="markFrom"]'
            human_clear(driver, start_record_input_xpath)
            start_record_input = driver.find_element(
                By.XPATH, start_record_input_xpath)
            human_type(start_record_input, str(start_record))
            print(f"提示：已输入起始记录号: {start_record}")
            verify_element_value(
                driver=driver, xpath=start_record_input_xpath, expected_value=start_record)

            # 清空并输入结束记录号
            end_record_input_xpath = '//input[@name="markTo"]'
            human_clear(driver, end_record_input_xpath)
            end_record_input = driver.find_element(
                By.XPATH, end_record_input_xpath)
            human_type(end_record_input, str(end_record))
            print(f"提示：已输入结束记录号: {end_record}")
            verify_element_value(
                driver=driver, xpath=end_record_input_xpath, expected_value=end_record)

            # 选择导出内容类型
            hover_pause_click(driver, '//button[@class="dropdown"]')
            hover_pause_click(
                driver, '//div/span[text()="Full Record and Cited References"]')
            print("提示：已选择导出内容类型")

            # 悬停并点击 "Export"
            hover_pause_click(
                driver, '//span[contains(@class, "ng-star-inserted") and text()="Export"]')
            print("提示：已点击导出确认按钮")

            if wos_export_dialog_exists(driver, wait_time=60):
                print("提示：导出对话自动框消失，任务成功")
                save_log(query_content, start_record, end_record,
                         download_task_log_path, "success")
                return True
            else:
                print("提示：导出对话框仍然存在，现点击“Cancel”并重新下载。")
                hover_pause_click(
                    driver, xpath_locator='//span[@class="mat-button-wrapper" and text()=\'Cancel \']')

        except Exception as e:
            print(f"提示：第 {attempt + 1} 次尝试下载失败，原因: {e}")
            if attempt == max_retries - 1:
                save_log(query_content, start_record, end_record,
                         download_task_log_path, "failure", str(e))
            else:
                print("提示：进入故障排查...")
                wos_detective_inspector(driver)
                if driver.current_url != url_query_result:
                    print("提示：当前 URL 与首次查询结果页不一致，现返回...")
                    driver.get(url_query_result)
                    random_scroll_partial(driver, ['down'], arrows=9)


def wos_log_query_task(query_content, start, end, total_records, download_task_log_path="."):
    """
    记录 Web of Science (WoS) 的查询任务到指定的文件。

    参数:
    - query_content: 查询内容，用于记录。
    - start: 用户指定的下载起始点。
    - end: 用户指定的下载结束点。
    - total_records: 总的记录数，用于记录。
    - download_task_log_path: 任务记录文件保存的路径，默认为当前路径。

    返回:
    None. 函数的目的是保存任务信息到一个文件中。
    """

    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    filename = os.path.join(download_task_log_path,
                            f"download_task_{timestamp}.json")

    task_info = {
        "query_content": query_content,
        "start_record": start,
        "end_record": end,
        "total_records": total_records,
        "timestamp": timestamp
    }

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(json.dumps(task_info, ensure_ascii=False, indent=4))


def wos_download_contractor(driver, query_content, start=1, end=None,
                            download_task_log_path=".", zhengzhengqiqi=True,
                            download_log_prefix="task_details__", wos_download_path="."):
    """
    对 Web of Science (WoS) 的查询结果进行自动化下载任务。

    参数:
    - driver: WebDriver 实例。
    - query_content: 查询内容，用于记录。
    - start: 用户指定的下载起始点，默认为 1。
    - end: 用户指定的下载结束点。如果没有指定，将使用查询结果的总记录数；如果指定的结束点超过查询结果的总记录数，会自动调整为查询结果最大值。
    - download_task_log_path: 下载任务和日志记录文件保存的路径，默认为当前路径。
    - zhengzhengqiqi: 布尔值，决定是否在下载完成后检查失败记录，并尝试重新下载它们。
    - download_log_prefix: 下载日志文件的前缀。
    - wos_download_path: WoS下载文件保存的路径。

    返回:
    None. 函数的目的是自动下载 WoS 的查询结果并根据指定的起始和结束点进行分段下载。
    """

    total_records = wos_query_result_count(driver)
    adjusted_end = end if end is not None and end <= total_records else total_records

    wos_log_query_task(query_content, start, adjusted_end,
                       total_records, download_task_log_path)

    download_ranges = wos_get_download_ranges(driver, start, adjusted_end)

    for start_record, end_record in download_ranges:
        wos_download_bricklayer(
            driver, query_content, start_record, end_record,
            download_task_log_path=download_task_log_path)
        time.sleep(get_power_law_pause(
            min_pause=3.42, max_pause=15, exponent=0.3))

    # 如果开启 zhengzhengqiqi 选项
    if zhengzhengqiqi:
        attempts = 3
        final_failed_records = None
        while attempts > 0:
            failed_records = aggregate_failed_records(
                download_task_log_path, query_content, download_log_prefix)
            if not failed_records or type(failed_records) == bool:
                break

            print(f"发现 {len(failed_records)} 个失败记录。尝试重新下载...")
            for start_record, end_record in failed_records:
                wos_download_bricklayer(
                    driver, query_content, start_record, end_record,
                    download_task_log_path=download_task_log_path)
                time.sleep(get_power_law_pause(
                    min_pause=3.42, max_pause=15, exponent=0.3))
            final_failed_records = failed_records
            attempts -= 1

        # 如果经过三次尝试还是失败
        if attempts == 0 and final_failed_records:
            with open(os.path.join(wos_download_path, "final_failed_records.json"), "w") as f:
                json.dump({
                    "query_content": query_content,
                    "failed_records": final_failed_records
                }, f)
            print("三次下载尝试失败，失败记录已保存到final_failed_records.json。")


def aggregate_failed_records(directory, query_content, file_prefix):
    """
    在给定目录中聚合具有指定前缀的json文件，并提取status字段不为'success'的记录。

    参数:
    - directory (str): 包含json文件的目录路径。
    - query_content (str): 查询内容。
    - file_prefix (str): 要聚合的json文件的前缀。

    返回:
    - list of tuple 或 bool: 一个(start_record, end_record)元组的列表或确认消息。
    """
    if not query_content:
        raise ValueError("必须提供 query_content 参数")
    if not file_prefix:
        raise ValueError("必须提供 file_prefix 参数")

    success_records = set()
    failed_records = set()

    # 列出目录中具有给定前缀的所有文件
    json_files = [f for f in os.listdir(directory) if f.startswith(
        file_prefix) and f.endswith('.json')]

    for json_file in json_files:
        with open(os.path.join(directory, json_file), 'r') as file:
            try:
                data = json.load(file)
                # 检查query_content是否匹配
                if data.get('query_content') == query_content:
                    record_tuple = (data['start_record'], data['end_record'])
                    if data.get('status') == 'success':
                        success_records.add(record_tuple)
                    else:
                        failed_records.add(record_tuple)
            except (json.JSONDecodeError, KeyError):
                print(f"处理文件 {json_file} 时遇到错误，跳过此文件。")
                continue

    # 从失败记录中剔除成功过的记录
    only_failed_records = failed_records - success_records

    if not only_failed_records:
        print("提示：未发现失败记录。")
        return True

    # 打印找到的失败记录次数
    print(f"提示：共找到 {len(only_failed_records)} 次失败记录。")

    # 返回排序后的失败记录列表
    return sorted(list(only_failed_records))


def find_and_move_files(source_path, target_path, journal_name):
    """
    从源路径查找与期刊名匹配的.txt和.json文件，并将它们移动到目标路径。

    参数:
    - source_path: 要搜索的源文件夹路径。
    - target_path: 移动文件的目标文件夹路径。
    - journal_name: 用于在.txt文件中匹配的期刊名称。

    返回:
    None. 该函数的目的是将匹配的文件从源路径移动到目标路径，并生成迁移日志。
    """

    so_pattern = re.compile(r'^SO (.+)$', re.MULTILINE)
    sn_pattern = re.compile(r'^SN (.+)$', re.MULTILINE)

    found_txt_files_count = 0
    found_json_files_count = 0
    moved_files_count = 0
    log_entries = []
    is_new_folder_generated = False
    folder_name = None
    validated_paths = set()

    for root, dirs, files in os.walk(source_path):
        # 先处理 .txt 文件
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.txt'):
                with open(filepath, 'r') as f:
                    content = f.read()
                    so_match = so_pattern.search(content)
                    sn_match = sn_pattern.search(content)

                    if so_match and journal_name.lower() in so_match.group(1).lower():
                        found_txt_files_count += 1
                        if sn_match and not is_new_folder_generated:
                            # 格式化文件夹名称
                            folder_name = f"{so_match.group(1).replace(' ', '_').replace('/', '_')}_ISSN{sn_match.group(1)}"
                            is_new_folder_generated = True

                        folder_path = os.path.join(target_path, folder_name)

                        if folder_path not in validated_paths:
                            validate_and_create_path(folder_path)
                            validated_paths.add(folder_path)

                        # 移动文件到新文件夹
                        shutil.move(filepath, os.path.join(folder_path, file))
                        log_entries.append(
                            f"Moved TXT {file} to {folder_path}")
                        moved_files_count += 1

        # 接着处理 .json 文件
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.json'):
                with open(filepath, 'r') as f:
                    content = json.load(f)
                    if "query_content" in content and journal_name.lower() in content["query_content"].lower():
                        found_json_files_count += 1
                        new_filename = f"{folder_name}_{file}" if folder_name else file
                        new_filepath = os.path.join(target_path, new_filename)
                        shutil.move(filepath, new_filepath)
                        log_entries.append(
                            f"Moved JSON {file} to {new_filepath}")
                        moved_files_count += 1

    # 写入日志
    log_filename = f"{folder_name}_migration_log.txt"
    with open(os.path.join(target_path, log_filename), "w") as log_file:
        log_file.write("Migration Log:\n")
        log_file.write(
            f"Total TXT files matching journal name: {found_txt_files_count}\n")
        log_file.write(
            f"Total JSON files matching journal name: {found_json_files_count}\n")
        log_file.write(f"Total files moved: {moved_files_count}\n\n")
        log_file.writelines("\n".join(log_entries))


def extract_content(s):
    """
    从字符串中提取内容。

    参数:
        s (str): 需要被提取内容的字符串。

    返回:
        str: 提取内容的大写。

    抛出异常:
        如果匹配失败，则抛出异常。
    """
    try:
        # 使用正则表达式提取内容
        match = re.search(r"SO=\((.*?)\)", s)

        if match:
            # 如果找到匹配内容，返回大写形式
            return match.group(1).upper()
        else:
            raise ValueError("未找到匹配内容。")
    except Exception as e:
        print(f"错误: {e}")
        raise


def set_browser_to_percentage_of_screen(driver, percentage=90, verbose=False):
    """
    根据给定的百分比设置 WebDriver 实例窗口的大小。

    参数:
    - driver: WebDriver 实例。
    - percentage: 实例窗口大小占显示器大小的百分比，范围从 1 到 100。默认为 80%。

    返回:
    无。函数会直接更改 WebDriver 实例的窗口大小。
    """
    try:
        monitor = get_monitors()[0]
        width = int(monitor.width * percentage / 100)
        height = int(monitor.height * percentage / 100)
        driver.set_window_size(width, height)
        print_verbose(
            message=f"提示:已设置实窗口为显示器尺寸的 %{percentage}", verbose=verbose)
    except Exception as e:
        print(f"错误:{e}")
