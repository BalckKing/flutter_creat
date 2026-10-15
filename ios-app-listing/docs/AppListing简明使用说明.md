# AppListing 简明使用说明

## 1. 使用前准备

- 仓库分支：`origin/feature/1.2.0`
- 在项目根目录执行相关命令
- 隐私协议参考：<https://codeup.aliyun.com/6366640f0cd435624679b545/Aurora/Agent/aurora_skills/ios-app-listing>

## 2. 推荐使用方式

直接对 Agent 发送下面这句提示词即可：

```text
只使用 ios-app-listing skill。为这个项目生成 AppListing，描述由当前 AI 直接编写，按仓库默认流程完成校验并部署 `AppListing/site/`。不要打开浏览器，不要请求本地 URL 预览，不要停下来等待额外交互确认，不要切到 brainstorming、visual companion 或其他交互式辅助流程，直接在工作区内完成。
```

默认流程包括：

1. 识别目标 iOS 项目
2. 生成 `AppListing` 文案和站点页面
3. 自动校验输出结果
4. 校验通过后部署 `AppListing/site/`

工作流接入建议：

- 如果这是自动化工作流，始终在提示词里显式要求“不要打开浏览器、不要请求本地 URL 预览、不要等待人工确认”
- 这个 skill 的正常路径应当只依赖仓库内脚本，不应把浏览器预览当成前置步骤
- 如果先要求方案，后续只要回复“执行 / 继续 / 发布出去”，Agent 应直接恢复 `ios-app-listing` 的执行流程，不再二次确认

## 3. 常用命令

如果需要手动执行，可以使用下面两个命令：

```bash
python3 scripts/inspect_app.py --target /path/to/app
python3 scripts/generate_app_listing.py --target /path/to/app
```

说明：

- `inspect_app.py` 用于识别项目能力、权限、IAP、AI 信号等信息
- `generate_app_listing.py` 用于生成 `AppListing/`，并在默认情况下自动部署
- 如果只想生成、不部署，可加 `--no-deploy-about`
- 这里的部署默认指远端 listing / legal 站点发布；除非明确要求，项目源码同步只替换已有 URL，不新增 App 内入口

示例：

```bash
python3 scripts/generate_app_listing.py --target /path/to/app --no-deploy-about
```

## 4. 生成结果

生成目录如下：

```text
AppListing/
  Intro.md
  site/
    index.html
    img/
      logo.png
    PrivacyPolicy.html
    Terms&Conditions.html
    Support.html
```

## 5. 注意事项

- `AppListing/site/` 是最终部署内容
- 部署成功后，`Intro.md` 中的占位 URL 会回填为真实线上地址
- 生成内容应以项目源码证据为准，不要手工补充无依据功能描述
