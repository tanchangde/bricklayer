# Bricklayer

Bricklayer,意为泥瓦匠,主要工作内容是搬砖抹灰砌墙.

## 动机

重复令人憎恨,尤其是 3202 年了都,GPT4 都能写代码了,还让人手动重复下载文件,不如把我嘎了.本项目基于 Python 下的 Selenium 实现了一个脚本,用于模拟人工自动化下载 Web of Science 引文数据.

## 环境配置

### Chrome

为模拟人工,避免被识别为机器人.同时提供可见的交互,用于低成本监控、介入下载任务.我们需要借助 Chrome.

请尽量确保你的 Chrome 版本在 114 及以上,本项目目前在 macOS 下的 `116.0.5845.96 (正式版本) (x86_64)` Chrome 上可以正常工作.

您可以在 Chrome 地址栏输入 `chrome://version/`, 以查看当前所使用 Chrome 版本,若您没有特殊的原因需要使用历史版本 Chrome,非常推荐更新到最新版本.

请尽量通过官方网站或可信软件市场安装 Chrome.

### ChromeDriver

请下载与 Chrome 版本号一致,且适用您所用操作系统的 ChromeDriver.最新的几个版本见 [Chrome for Testing availability](https://googlechromelabs.github.io/chrome-for-testing/).

对于 macOS,请参考 [How to Install Chrome Driver on Mac](https://www.swtestacademy.com/install-chrome-driver-on-mac/#:~:text=Unable%20to%20launch%20the%20chrome,chromeDriver%20file%20and%20open%20it.),将 `chromedriver` 可执行文件移动到 `/usr/local/bin`.

注意,若您不了解文中的终端命令如何执行,请转为使用访达的`前往`功能,前往 `/usr/local/bin` 文件夹.

这样可以让我们在后续调用 `chromedriver` 时,省略指定 `chromedriver` 所在路径.

### Visual Studio Code

本项目样例,使用 `ipynb` 文件,即 `Jupyter Notebooks` 提供.所以,我们需要一个支持这种文件的编辑器.这里推荐 Visual Studio Code,微软出品,下限有保障.当然,您也可以采用你熟悉的工具.

关于在 VS Code 中使用 `Jupyter Notebooks`,请优先参考 [Working with Jupyter Notebooks in Visual Studio Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

安装好 VS Code 之后,利用其打开 Python 文件或 Jupyter 文件时.VS Code 会提示安装相关的官方插件,不要犹豫,安装即可.

### 复现项目环境

为了确保您能够正确地复现 Python 项目的环境,以下简明操作指南,将会指导您如何使用 `requirements.txt` 或 `environment.yml` 在 macOS 上配置环境.

1. **安装 Anaconda 或 Miniconda**
  
    如果您还没有安装 Anaconda 或 Miniconda,可以选择其一进行安装.若果没有重度的数据科学相关使用,推荐更轻量的 Miniconda.:

    * [Anaconda下载页面](https://www.anaconda.com/products/distribution#download-section)
    * [Miniconda下载页面](https://docs.conda.io/en/latest/miniconda.html)

2. **创建环境**
  
    在终端中,进入到项目的目录:

    ```bash
    cd path/to/your/project
    ```

    使用 `environment.yml` 创建 Conda 环境:

    ```bash
    conda env create -f environment.yml
    ```

3. **激活环境**

    创建环境后,它通常会有一个名称（您可以在 `environment.yml` 文件的第一行找到它,它紧跟在 `name:` 之后）.假设名称为 `myenv`,您可以这样激活它:

    ```bash
    conda activate myenv
    ```

## 用例

请参考 [Demo](demo.ipynb).

## ChangeLog

* 230823,长德新建
* 230825,重写 Python 环境配置
* 230116
  * 更新项目环境复现文件
