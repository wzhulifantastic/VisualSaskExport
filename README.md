# VisualSaskExport - 萨斯喀彻温省农业出口数据可视化工具

## 项目概述

VisualSaskExport 是一个针对加拿大萨斯喀彻温省（Saskatchewan）农业出口数据的可视化分析工具。该项目结合了 Python 数据处理、Jupyter Notebook 交互式分析和 Web 可视化界面，帮助用户理解和探索农业出口趋势。Data Source：Canadian International Merchandise Trade Web Application中Exports的Data extraction。

## 项目结构

```
.
├── main.py                    # 主程序入口
├── pyproject.toml            # Python 项目配置
├── uv.lock                   # 依赖锁定文件
├── .python-version          # Python 版本指定
├── index.html               # Web 可视化界面
├── export_data.json         # 导出的可视化数据
├── CA-CN2024-2025report.csv # 加拿大-中国农业出口报告数据
├── VisualSaskExport_AgExport.ipynb      # 主分析 Notebook
├── VisualSaskExport_AgExport - 折线.ipynb # 折线图分析 Notebook
├── .gitignore               # Git 忽略配置
├── README.md                # 项目文档（当前文件）
└── .venv/                   # Python 虚拟环境
```

## 功能特性

1. **数据预处理** - 清洗和转换原始 CSV 数据为结构化格式
2. **趋势分析** - 分析农业出口的时间序列趋势
3. **可视化生成** - 创建折线图、柱状图等多种图表
4. **交互式探索** - 通过 Jupyter Notebook 进行数据探索
5. **Web 展示** - 将分析结果通过 HTML 页面展示
6. **数据导出** - 将处理后的数据导出为 JSON 格式

## 使用步骤

### 步骤 1：环境设置
```bash
# 使用 uv 创建虚拟环境（推荐）
uv sync

# 或使用传统方式
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
pip install -e .
```

### 步骤 2：数据准备
- 将原始数据文件（如 `SK-CN_2024-2025Oct_Report.csv`）放置在项目根目录
- 数据应包含时间序列、产品类别、出口量等字段

### 步骤 3：运行分析
```bash
# 运行主程序
python main.py

# 或打开 Jupyter Notebook 进行交互式分析
jupyter notebook VisualSaskExport_AgExport.ipynb
```

### 步骤 4：查看结果
- 分析结果将保存在 `export_data.json` 中
- 打开 `index.html` 查看可视化图表
- 检查生成的图表和报告

## 架构说明

### 1. 数据层（Data Layer）
- **功能**：负责数据的读取、清洗和存储
- **组件**：CSV 解析器、数据验证器、JSON 导出器
- **文件**：`SK-CN_2024-2025Oct_Report.csv`, `export_data.json`

### 2. 分析层（Analysis Layer）
- **功能**：执行核心数据分析算法和计算
- **组件**：趋势分析器、统计计算器、数据转换器
- **文件**：`VisualSaskExport_AgExport.ipynb`, Python 分析模块

### 3. 可视化层（Visualization Layer）
- **功能**：将数据转换为可视化图表
- **组件**：图表生成器、样式管理器、交互处理器
- **文件**：`index.html`, 图表生成代码

### 4. 表示层（Presentation Layer）
- **功能**：提供用户界面和交互体验
- **组件**：Web 界面、Notebook 界面、报告生成器
- **文件**：`index.html`, Jupyter Notebooks

### 5. 工具层（Utility Layer）
- **功能**：提供辅助功能和项目配置
- **组件**：环境配置、依赖管理、项目设置
- **文件**：`pyproject.toml`, `uv.lock`, `.gitignore`

## 数据流程

```
原始 CSV 数据 → 数据清洗 → 分析处理 → 可视化生成 → Web 展示
      ↓            ↓           ↓           ↓           ↓
    Export      Python脚本   Jupyter     图表库      HTML/JS
    report          or       Notebook     页面
    .csv         Notebook
```

## 依赖与安装

### 核心依赖
- Python 3.12+（由 `.python-version` 指定）
- pandas - 数据处理
- matplotlib / plotly - 数据可视化
- jupyter - 交互式分析环境

### 安装方式
```bash
# 使用 uv（推荐）
uv pip install -e .

# 或使用 pip
pip install -r requirements.txt
```

## 示例使用场景

1. **农业出口趋势分析**：分析特定农产品对中国的出口趋势
2. **年度报告生成**：生成年度农业出口可视化报告
3. **数据探索**：交互式探索不同时间段的出口数据
4. **教学演示**：作为数据科学和可视化教学案例

## 开发说明

### 代码结构
- 主程序入口：`main.py` - 简单的演示程序
- 核心分析：Jupyter Notebooks - 包含完整的数据分析流程
- 数据文件：CSV 和 JSON - 存储原始数据和处理结果
- Web 界面：HTML/JavaScript - 展示最终可视化结果

### 扩展方向
1. 添加更多数据源和处理模块
2. 实现自动化报告生成
3. 构建完整的 Web 应用后端
4. 添加用户认证和数据管理功能

## 许可证

本项目采用 MIT 许可证。

---

*项目创建者：wzhulifantastic*  
*GitHub 仓库：https://github.com/wzhulifantastic/VisualSaskExport*  
*最后更新：2026年1月*
