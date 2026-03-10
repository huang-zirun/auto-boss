# 自动Git推送 Skill

## 元数据

```yaml
name: auto-git-push
description: 当用户需要将代码推送到远程Git仓库时，自动执行持续推送操作，直到成功为止。适用于网络不稳定或推送经常失败的场景。
```

## 触发条件

当用户需要推送代码到远程Git仓库，且希望系统自动处理网络波动导致的推送失败时。

## 执行步骤

1. **检查Git状态**：确认本地仓库是否有未推送的提交
2. **执行推送循环**：
   - 显示"尝试推送..."的提示信息
   - 执行`git push`命令
   - 检查命令执行结果
   - 如果推送成功，显示"推送成功！"并退出循环
   - 如果推送失败，显示"推送失败，5秒后重试..."并等待5秒后重新尝试

## 实现代码

```powershell
while ($true) {
    Write-Host '尝试推送...' -ForegroundColor Green
    git push
    if ($LASTEXITCODE -eq 0) {
        Write-Host '推送成功！' -ForegroundColor Green
        break
    } else {
        Write-Host '推送失败，5秒后重试...' -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
}
```

## 输出结果

- **成功**：显示"推送成功！"的绿色提示信息，推送过程完成
- **失败**：显示"推送失败，5秒后重试..."的红色提示信息，继续尝试推送

## 注意事项

- 此Skill会持续运行直到推送成功，适用于网络不稳定的环境
- 请确保本地仓库已正确配置远程仓库地址
- 请确保本地仓库有可推送的提交