# NovelTuner 📚

NovelTuner 是一个网络小说处理工具集，提供 EPUB 图片修复、繁简转换、文本换行修复等多种文本处理功能。项目采用统一的管理系统，通过主脚本访问所有工具。

## 🌟 功能特性

### 📖 EPUB 图片修复工具 (image_fixer)
- **自动图片下载**：检测并下载 EPUB 文件中缺失的图片
- **链接修复**：将 `<图片>` 标签转换为标准的 `<img>` 标签
- **批量处理**：支持单个文件或整个目录的批量处理
- **递归处理**：支持递归处理子目录中的所有 EPUB 文件
- **智能重试**：下载失败时自动重试，确保稳定性

### 🈳 繁简转换工具 (traditional_to_simplified)
- **繁体转简体**：将繁体中文文本转换为简体中文
- **批量转换**：支持单个文件或批量目录处理
- **递归处理**：支持递归处理子目录中的所有文本文件
- **可选备份**：可选择创建备份文件（使用 `-b` 参数）
- **编码自动检测**：支持 UTF-8、GBK、Big5 等多种编码

### 📝 文本换行修复工具 (fix_line_breaks)
- **智能合并**：自动检测并修复中文文本中的异常换行（一行以汉字结尾，下一行以汉字开始）
- **连续合并**：支持连续多行的智能合并，解决复杂的换行问题
- **标点符号识别**：正确处理句号、感叹号、问号等标点符号，避免错误合并
- **批量处理**：支持单个文件或整个目录的批量处理
- **递归处理**：支持递归处理子目录中的所有文本文件
- **可选备份**：可选择创建备份文件（使用 `-b` 参数）

### 🔧 统一管理系统 (novel_tuner.py)
- **自动工具发现**：自动扫描 `tools/` 目录下的所有有效工具
- **动态工具加载**：使用改进的导入机制，避免模块缓存问题
- **统一接口验证**：确保所有工具实现标准接口
- **智能参数解析**：正确处理工具特定的命令行参数
- **错误处理和日志**：详细的错误信息和堆栈跟踪

## 🚀 快速开始

### 环境要求
- Python 3.7 或更高版本
- 相关依赖库（见下方安装说明）

### 安装依赖

在项目根目录下运行以下命令安装所有依赖：

```bash
pip install -r requirements.txt
```

## 📋 使用说明

### 统一管理系统（推荐）

项目采用统一的管理系统，通过 `novel_tuner.py` 主脚本访问所有工具：

```bash
# 查看可用工具
python novel_tuner.py --list-tools

# 使用工具
python novel_tuner.py <tool_name> <input> [options]

# 获取工具帮助
python novel_tuner.py <tool_name> --help
```

### 基本用法

```bash
# 查看所有可用工具
python novel_tuner.py --list-tools

# 获取工具帮助
python novel_tuner.py fix_line_breaks --help

# 修复单个文件的换行问题
python novel_tuner.py fix_line_breaks input.txt -o output.txt

# 批量处理目录中的txt文件
python novel_tuner.py fix_line_breaks novel_dir -r -f txt

# 繁简转换（支持自动编码检测）
python novel_tuner.py traditional_to_simplified traditional.txt -o simplified.txt

# 带备份的批量处理
python novel_tuner.py fix_line_breaks input_dir -r -b -v
```

### 高级用法

```bash
# 自定义文件扩展名
python novel_tuner.py fix_line_breaks docs/ -r -f txt,md,log

# 自定义标点符号（换行修复）
python novel_tuner.py fix_line_breaks input.txt --punctuation "。！？：；"

# 指定编码进行繁简转换
python novel_tuner.py traditional_to_simplified input.txt --encoding gbk

# 静默模式（仅显示错误）
python novel_tuner.py fix_line_breaks input.txt -q
```

### 传统用法（直接调用工具）

所有工具都遵循统一的参数标准：

```bash
# 基本使用（处理单个文件，不创建备份）
python tools/fix_line_breaks.py input.file

# 指定输出文件
python tools/fix_line_breaks.py input.file -o output.file

# 递归处理目录
python tools/fix_line_breaks.py input_dir/ -r

# 创建备份
python tools/fix_line_breaks.py input.file -b
```

## 📦 依赖说明

### 主要依赖
- **requests**: HTTP 请求库，用于下载图片
- **beautifulsoup4**: HTML/XML 解析库
- **Pillow**: 图像处理库
- **opencc-python-reimplemented**: 繁简中文转换库
- **tqdm**: 进度条显示库
- **charset-normalizer**: 编码检测库

### 安装所有依赖
```bash
pip install -r requirements.txt
```

### 依赖详情
项目已整合所有必要依赖，包括：
- **文件操作工具**：批量文件处理、路径管理、安全文件写入
- **编码检测工具**：自动编码检测、多编码支持、容错处理
- **备份管理工具**：带时间戳的备份、备份清理、恢复功能
- **命令行工具**：统一参数标准、输入验证、进度显示

## 🎯 使用场景

### EPUB 图片修复
- 修复来自网络小说的 EPUB 文件中的图片链接
- 下载缺失的图片并更新引用
- 确保图片在电子书阅读器中正常显示

### 繁简转换
- 将台湾、香港等地区的繁体中文小说转换为简体中文
- 批量处理大量文本文件
- 保持原有格式不变，仅转换字符

### 文本换行修复
- 修复网络小说中因复制粘贴导致的异常换行问题
- 将错误分段的中文句子重新合并为完整段落
- 保持对话、引用等特殊格式的完整性
- 适用于各种中文文本文件

## 📁 文件结构
```
NovelTuner/
├── novel_tuner.py              # 统一管理系统主脚本
├── tools/                      # 文本处理工具目录
│   ├── __init__.py
│   ├── fix_line_breaks.py      # 中文换行修复工具
│   ├── traditional_to_simplified.py  # 繁简转换工具
│   └── image_fixer.py          # EPUB图片下载修复工具
├── utils/                      # 公共工具函数
│   ├── __init__.py
│   ├── file_utils.py           # 文件操作工具
│   ├── encoding_utils.py       # 编码检测工具
│   ├── backup_utils.py         # 备份管理工具
│   └── cli_utils.py            # 命令行工具
├── requirements.txt            # Python依赖
├── CLAUDE.md                   # 项目规范文档
└── README.md                   # 项目说明文档
```

## 🛠️ 技术特性

### 统一管理系统
- **智能参数解析**：正确处理工具特定的命令行参数，避免冲突
- **改进的导入机制**：使用 `importlib.util` 避免模块缓存问题
- **详细的错误报告**：提供具体的错误信息和缺失的接口函数
- **ASCII安全输出**：避免Windows控制台的编码问题

### 公共工具函数
- **文件操作**：统一的文件批量处理、路径管理、安全写入
- **编码处理**：支持UTF-8、GBK、Big5等多种编码的自动检测和容错
- **备份管理**：带时间戳的备份、自动清理、恢复功能
- **CLI标准化**：统一的参数标准、输入验证、进度显示

### 工具接口标准化
- **统一参数标准**：所有工具支持 `-o, -r, -b, -v, -q` 等通用参数
- **模块化设计**：工具间无依赖，可独立使用
- **错误处理**：统一的异常处理和用户反馈

## ⚠️ 注意事项

1. **统一管理系统**：推荐使用 `novel_tuner.py` 主脚本访问所有工具
2. **文件备份**：默认不创建备份文件，如需备份请使用 `-b` 参数
3. **网络连接**：EPUB 图片修复需要网络连接以下载图片
4. **文件权限**：确保有足够的文件读写权限
5. **临时文件**：处理过程中会创建临时文件，程序会自动清理
6. **编码格式**：系统支持自动编码检测，可处理 UTF-8、GBK、Big5 等多种编码
7. **文本换行修复**：该工具专门针对中文文本设计，对其他语言可能不适用


### 📋 待优化
- 多步调用支持（单次调用执行多个工具）
- 性能优化（错误重试优化）
- 扩展功能（新工具开发）
- 综合测试套件完善

## 🤝 贡献指南

欢迎贡献新的文本处理工具！请遵循以下步骤：

1. 在 `tools/` 目录下创建新的工具模块
2. 实现标准接口（`get_description`, `get_parser`, `main`）
3. 使用 `utils/` 中的公共函数处理文件和编码
4. 添加适当的测试用例
5. 更新文档和示例