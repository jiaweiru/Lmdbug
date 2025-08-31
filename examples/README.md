# Lmdbug Examples

这个目录包含了 Lmdbug 的使用示例，展示如何创建包含音频和文本数据的 LMDB 数据库，以及如何使用自定义处理器进行预览。

## 📁 文件说明

- `sample_proto.proto` - Protocol Buffers 定义文件
- `sample_proto_pb2.py` - 编译后的 Python protobuf 类
- `create_sample_db.py` - 创建示例数据库的脚本
- `sample_lmdb_demo/` - 生成的示例 LMDB 数据库

## 🚀 快速开始

### 1. 生成 protobuf Python 代码 (已完成)

```bash
# 已生成，无需重复执行
protoc --python_out=. sample_proto.proto
```

### 2. 创建示例数据库

```bash
python examples/create_sample_db.py examples/sample_lmdb_demo
```

这将创建一个包含以下内容的 LMDB 数据库：
- **3个 User protobuf 消息**，每个包含：
  - `description` 字段：长文本内容（用于文本预览）
  - `voice_audio` 字段：Base64 编码的 24kHz 16-bit PCM 音频数据（用于音频预览）
  - 其他字段：username, email, tags, 等

### 3. 启动 Lmdbug

```bash
lmdbug --db-path examples/sample_lmdb_demo \
       --protobuf-module examples/sample_proto_pb2.py \
       --message-class User
```

### 4. 探索数据

在 Lmdbug 网页界面中，尝试搜索以下模式：

- `proto:user:` - 包含音频和文本数据的用户消息
- `json:user:` - 纯 JSON 用户数据（对比）
- `config:` - 配置条目
- `stats:` - 统计数据
- `test:item:` - 测试条目

## 🎵 媒体预览功能

当你浏览 `proto:user:*` 条目时，你会看到：

### 📝 文本预览
- 字段：`description`
- 处理器：`text_description` (在 `config_examples/custom_processors.py`)
- 显示：截断的文本内容和字符数

### 🔊 音频预览
- 字段：`voice_audio`
- 处理器：`pcm_24khz_16bit` (在 `config_examples/custom_processors.py`)
- 功能：将 Base64 PCM 数据转换为可播放的 WAV 文件

## 🔧 自定义处理器

查看 `../config_examples/custom_processors.py` 了解处理器实现：

1. **TextDescriptionProcessor** - 处理文本描述字段
   - 支持字段：description, bio, content, text, message
   - 创建文本预览，包含字符统计

2. **Pcm24khzProcessor** - 处理 PCM 音频数据
   - 支持字段：以 'audio' 或 'pcm' 结尾的字段
   - 将 Base64 PCM 转换为 WAV 文件，供网页播放

## 📊 数据结构

示例数据库包含 28 个条目：

```
proto:user:1, proto:user:2, proto:user:3  # 用户 protobuf 数据
json:user:101, json:user:102               # JSON 对比数据  
config:app:version, config:app:environment # 配置数据
stats:users:total, stats:sessions:current  # 统计数据
test:item:0000 - test:item:0014            # 测试条目
```

## 🎯 学习目标

通过这个示例，你可以学习到：

1. **Protobuf 集成** - 如何定义和使用 protobuf 消息
2. **音频处理** - 如何处理二进制音频数据
3. **文本预览** - 如何创建长文本的预览
4. **处理器开发** - 如何编写自定义字段处理器
5. **LMDB 操作** - 如何存储和检索复杂数据

享受探索 Lmdbug 的功能吧！ 🎉