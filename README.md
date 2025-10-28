# Blender DXF Importer (Community Version)

[![License: GPL v2 or later](https://img.shields.io/badge/License-GPL%20v2%2B-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Blender](https://img.shields.io/badge/Blender-%23F5792A.svg?style=flat&logo=blender&logoColor=white)](https://www.blender.org/)

## 项目说明

本仓库是 Blender 的 DXF 导入插件的社区维护版本，基于 DeepSeek 的代码研究创建。这个插件允许用户在 Blender 中直接导入 AutoCAD DXF 格式（.dxf）文件。

## 功能特点

- 支持导入 DXF 文件到 Blender
- 保持与原始 CAD 设计的兼容性
- 社区驱动，持续维护更新
- 支持 Blender 4.2 及以上版本
- 新增按图层集合分组功能
- 新增按图层颜色自动着色功能
- 新增直接转换曲线为松散边功能
## 问题
- 某些 DXF 文件导入后，按曲线解析越界，导致导入失败
- 曲线按松散边解析后，缺失部分线条
- 当前解析逻辑缺乏某些线条，从建模角度来说影响不大，从还原CAD渲染来说需要修复

## 安装方法

1. 下载最新版本的插件 ZIP 文件
2. 在 Blender 中打开 `编辑(Edit)` > `偏好设置(Preferences)` > `插件(Add-ons)`
3. 点击 `安装(Install)...` 按钮
4. 选择下载的 ZIP 文件并启用插件

## 使用方法

1. 在 Blender 中，点击 `文件(File)` > `导入(Import)` > `AutoCAD DXF (.dxf)`
2. 选择要导入的 DXF 文件
3. 调整导入选项（如需要）
4. 点击 `导入 DXF` 按钮

## 系统要求

- Blender 4.2 或更高版本
- Python 3.x

## 贡献指南

欢迎提交 Pull Request 或报告问题。在贡献代码前，请确保：

1. 代码符合 PEP 8 规范
2. 添加适当的测试用例
3. 更新相关文档

## 许可证

本项目采用 [GNU General Public License v2.0 或更高版本](LICENSE) 授权。

## 致谢

- 感谢所有贡献者的辛勤工作
- 特别感谢 DeepSeek 在代码研究方面提供的支持
- 基于 [dxfgrabber](https://github.com/mozman/dxfgrabber) 库开发

## 相关链接

- [Blender 官方网站](https://www.blender.org/)
- [项目讨论区](https://projects.blender.org/extensions/io_import_dxf)
- [DXF 格式规范](https://www.autodesk.com/techpubs/autocad/acad2000/dxf/)

---

*注意：此插件为社区维护版本，不隶属于 Autodesk 或 Blender 基金会官方项目。*
