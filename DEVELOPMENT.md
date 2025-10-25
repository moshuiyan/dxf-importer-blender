# Blender DXF Importer 开发文档

## 目录
1. [项目概述](#项目概述)
2. [代码结构](#代码结构)
3. [核心组件](#核心组件)
4. [开发环境设置](#开发环境设置)
5. [开发指南](#开发指南)
6. [测试方法](#测试方法)
7. [贡献指南](#贡献指南)
8. [调试技巧](#调试技巧)
9. [发布流程](#发布流程)

## 项目概述

Blender DXF 导入插件是一个用于将 AutoCAD DXF 格式文件导入到 Blender 中的工具。它支持多种 DXF 实体类型，包括线条、多段线、圆、圆弧、文本等，并提供了多种导入选项以控制导入过程。

## 代码结构

```
.
├── __init__.py           # Blender 插件主入口
├── dxfimport/           # DXF 导入核心实现
│   ├── do.py            # 主要导入逻辑
│   ├── entities.py      # DXF 实体处理
│   ├── fake_entities.py # 模拟 DXF 实体
│   └── is_.py           # 实体类型判断
├── dxfgrabber/          # DXF 解析库
│   ├── __init__.py
│   ├── const.py         # 常量定义
│   ├── drawing.py       # DXF 文档表示
│   ├── dxfentities.py   # DXF 实体定义
│   ├── dxfobjects.py    # DXF 对象定义
│   ├── entitysection.py # 实体段处理
│   ├── headersection.py # 头段处理
│   ├── sections.py      # DXF 段处理
│   └── tags.py          # DXF 标签处理
└── transverse_mercator.py  # 横轴墨卡托投影工具
```

## 核心组件

### 1. 插件入口 (__init__.py)
- 定义 Blender 操作符 `IMPORT_OT_dxf`
- 处理用户界面和导入参数
- 注册/注销插件

### 2. DXF 导入核心 (dxfimport/do.py)
- `Do` 类：处理 DXF 导入的主要逻辑
- 实体转换和场景构建
- 处理块引用和实例化

### 3. DXF 解析 (dxfgrabber/)
- 提供 DXF 文件的低级解析功能
- 支持多种 DXF 版本
- 将 DXF 结构转换为 Python 对象

## 开发环境设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/import_autocad_dxf_format_dxf.git
   ```

2. 安装依赖：
   ```bash
   pip install pyproj
   ```

3. 链接到 Blender 插件目录：
   ```bash
   # Linux/macOS
   ln -s /path/to/import_autocad_dxf_format_dxf ~/.config/blender/4.2/scripts/addons/import_autocad_dxf_format_dxf
   
   # Windows
   mklink /D "%APPDATA%\Blender Foundation\Blender\4.2\scripts\addons\import_autocad_dxf_format_dxf" "E:\GitHub\import_autocad_dxf_format_dxf"
   ```

## 开发指南

### 添加新实体支持

1. 在 `dxfimport/entities.py` 中添加新的实体处理函数
2. 在 `Do` 类中注册实体处理函数
3. 添加相应的单元测试

### 处理坐标变换

坐标变换在 `transverse_mercator.py` 中实现，支持地理参考坐标到 Blender 世界坐标的转换。

### 调试导入问题

1. 启用调试模式：在 `__init__.py` 中设置 `DEBUG = True`
2. 查看 Blender 控制台输出
3. 使用 `print` 或 `logging` 添加调试信息

## 测试方法

1. 单元测试：
   ```bash
   cd tests
   python -m unittest discover
   ```

2. 手动测试：
   - 在 Blender 中导入各种 DXF 文件
   - 测试不同导入选项
   - 验证几何体正确性

## 贡献指南

1. Fork 仓库并创建特性分支
2. 提交清晰的提交信息
3. 确保代码符合 PEP 8 规范
4. 添加或更新测试
5. 创建 Pull Request

## 调试技巧

1. 使用 Blender 的 Python 控制台进行交互式调试
2. 检查 Blender 的系统控制台输出
3. 使用 `bpy.app.debug = True` 启用 Blender 调试模式
4. 检查 DXF 文件中的特定实体：
   ```python
   import dxfgrabber
   dwg = dxfgrabber.read("test.dxf")
   print([e for e in dwg.entities if e.dxftype == 'YOUR_ENTITY_TYPE'])
   ```

## 发布流程

1. 更新版本号：
   - `__init__.py` 中的 `bl_info['version']`
   - `blender_manifest.toml` 中的 `version` 字段

2. 创建发布分支：
   ```bash
   git checkout -b release/vX.Y.Z
   ```

3. 创建发布标签：
   ```bash
   git tag -a vX.Y.Z -m "Version X.Y.Z"
   git push origin vX.Y.Z
   ```

4. 创建 GitHub 发布版本并上传打包的插件

## 常见问题

### 1. 导入速度慢
- 尝试禁用不必要的导入选项
- 检查是否有复杂的块定义
- 考虑使用更简单的几何体表示

### 2. 坐标不准确
- 检查 DXF 文件的单位和比例
- 验证坐标变换参数
- 检查是否有地理参考信息需要处理

### 3. 实体丢失
- 检查 DXF 版本兼容性
- 验证实体类型是否受支持
- 检查图层可见性设置

## 资源

- [DXF 格式规范](https://www.autodesk.com/techpubs/autocad/acad2000/dxf/)
- [Blender Python API 文档](https://docs.blender.org/api/current/)
- [dxfgrabber 文档](https://github.com/mozman/dxfgrabber)

---

*注意：本文档会随着项目发展而更新，请定期查看最新版本。*
