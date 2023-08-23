# Bricklayer

Bricklayer，意为泥瓦匠，主要工作内容是搬砖抹灰砌墙。

## 动机

重复令人憎恨，尤其是 3202 年了都，GPT4 都能写代码了，还让人手动重复下载文件，不如把我嘎了。本项目基于 Python 下的 Selenium 实现了一个脚本，用于模拟人工自动化下载 Web of Science 引文数据。

## 环境配置

### 安装 Chrome

为模拟人工，避免被识别为机器人。同时提供可见的交互，用于低成本监控、介入下载任务。我们需要借助 Chrome。

请尽量确保你的 Chrome 版本在 114 及以上，本项目目前在 macOS 下的 `116.0.5845.96 (正式版本) (x86_64)` Chrome 上可以正常工作。

您可以在 Chrome 地址栏输入 `chrome://version/`， 以查看当前所使用 Chrome 版本，若您没有特殊的原因需要使用历史版本 Chrome，非常推荐更新到最新版本。

请尽量通过官方网站或可信软件市场安装 Chrome。

### 下载 ChromeDriver

请下载与 Chrome 版本号一致，且适用您所用操作系统的 ChromeDriver。最新的几个版本见 [Chrome for Testing availability](https://googlechromelabs.github.io/chrome-for-testing/)。

对于 macOS，请参考 [How to Install Chrome Driver on Mac](https://www.swtestacademy.com/install-chrome-driver-on-mac/#:~:text=Unable%20to%20launch%20the%20chrome,chromeDriver%20file%20and%20open%20it.)，将 `chromedriver` 可执行文件移动到 `/usr/local/bin`。

注意，若您不了解文中的终端命令如何执行，请转为使用访达的`前往`功能，前往 `/usr/local/bin` 文件夹。

这样可以让我们在后续调用 `chromedriver` 时，省略指定 `chromedriver` 所在路径。

### Visual Studio Code

本项目样例，使用 `ipynb` 文件，即 `Jupyter Notebooks` 提供。所以，我们需要一个支持这种文件的编辑器。这里推荐 Visual Studio Code，微软出品，下限有保障。当然，您也可以采用你熟悉的工具。

关于在 VScode 中使用 `Jupyter Notebooks`，请优先参考 [Working with Jupyter Notebooks in Visual Studio Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)。

### Python

本代码目前在 `Python 3.9.13` 上测试通过，若你当前的 Python 版本不能正常运行本代码，请利用熟悉的 Python 环境管理工具，安装测试通过的版本。若你没有熟悉的工具，这里推荐 [Miniconda — conda documentation](https://docs.conda.io/en/latest/miniconda.html)，其体积较小。

环境管理工具安装后，请利用环境管理工具，创建并激活特定版本的 Python 虚拟环境。然后通过运行 [Demo](demo.ipynb) “导入预定义函数”的代码块，参考报错提示哪些包没有安装，然后在你创建的 Python 虚拟环境安装这些包。

特别注意，Conda 收录的包 `undetected_chromedriver`，在最新版的 chromedriver 上可能存在 Bug。请参考 [Add support for downloading Chromedriver versions 115+](https://github.com/ultrafunkamsterdam/undetected-chromedriver/pull/1478)，按装修复版本。

## 用例

请参考 [Demo](demo.ipynb).

## ChangeLog

* 230823，长德新建
