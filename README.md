# NovelTuner 📚

NovelTuner 是一个网络小说处理工具集，提供 EPUB 图片修复、繁简转换、文本换行修复等多种文本处理功能。

## 🌟 功能特性

### 📖 EPUB 图片修复工具 (image_fixer.py)
- **自动图片下载**：检测并下载 EPUB 文件中缺失的图片
- **链接修复**：将 `<图片>` 标签转换为标准的 `<img>` 标签
- **批量处理**：支持单个文件或整个目录的批量处理
- **递归处理**：支持递归处理子目录中的所有 EPUB 文件
- **智能重试**：下载失败时自动重试，确保稳定性

### 🈳 繁简转换工具 (traditional_to_simplified.py)
- **繁体转简体**：将繁体中文文本转换为简体中文
- **批量转换**：支持单个文件或批量目录处理
- **递归处理**：支持递归处理子目录中的所有文本文件
- **可选备份**：可选择创建备份文件（使用 `-b` 参数）

### 📝 文本换行修复工具 (fix_line_breaks.py)
- **智能合并**：自动检测并修复中文文本中的异常换行（一行以汉字结尾，下一行以汉字开始）
- **连续合并**：支持连续多行的智能合并，解决复杂的换行问题
- **标点符号识别**：正确处理句号、感叹号、问号等标点符号，避免错误合并
- **批量处理**：支持单个文件或整个目录的批量处理
- **递归处理**：支持递归处理子目录中的所有文本文件
- **可选备份**：可选择创建备份文件（使用 `-b` 参数）

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

所有工具都遵循统一的参数标准：

```bash
# 基本使用（处理单个文件，不创建备份）
python script.py input.file

# 指定输出文件
python script.py input.file -o output.file

# 递归处理目录
python script.py input_dir/ -r

# 输出到指定目录
python script.py input_dir/ -o output_dir/

# 创建备份
python script.py input.file -b
```

### 工具特定用法

#### EPUB 图片修复工具
```bash
# 处理 EPUB 文件
python image_fixer.py input.epub
python image_fixer.py input_dir/ -r -b
```

#### 繁简转换工具
```bash
# 转换文本文件
python traditional_to_simplified.py input.txt
python traditional_to_simplified.py input_dir/ -r -o output_dir/
```

#### 文本换行修复工具
```bash
# 修复文本换行
python fix_line_breaks.py input.txt
python fix_line_breaks.py input_dir/ -r -f txt,md
```

### 查看帮助
```bash
python image_fixer.py --help
python traditional_to_simplified.py --help
python fix_line_breaks.py --help
```

## 📦 依赖说明

### 主要依赖
- **requests**: HTTP 请求库，用于下载图片
- **beautifulsoup4**: HTML/XML 解析库
- **Pillow**: 图像处理库
- **opencc-python-reimplemented**: 繁简中文转换库
- **tqdm**: 进度条显示库

### 文本换行修复工具
该工具为纯 Python 实现，无需额外依赖，仅使用标准库即可运行。

### 安装所有依赖
```bash
pip install requests beautifulsoup4 pillow opencc-python-reimplemented tqdm
```

或者使用 requirements.txt：
```bash
pip install -r requirements.txt
```

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
├── image_fixer.py              # EPUB 图片修复工具
├── traditional_to_simplified.py # 繁简转换工具
├── fix_line_breaks.py          # 文本换行修复工具
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明文档
```

## ⚠️ 注意事项

1. **文件备份**：默认不创建备份文件，如需备份请使用 `-b` 参数
2. **网络连接**：EPUB 图片修复需要网络连接以下载图片
3. **文件权限**：确保有足够的文件读写权限
4. **临时文件**：处理过程中会创建临时文件，程序会自动清理
5. **编码格式**：所有工具均使用 UTF-8 编码，请确保文件编码正确
6. **文本换行修复**：该工具专门针对中文文本设计，对其他语言可能不适用