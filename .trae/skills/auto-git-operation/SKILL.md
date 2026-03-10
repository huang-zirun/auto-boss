---
name: "auto-git-operation"
description: "Automatically performs Git push or pull operations with retry mechanism. Invoke when user needs to push or pull code and wants to handle network failures automatically."
---

# Auto Git Operation

## When to Use

Use this skill when:
- User needs to push code to remote Git repository
- User needs to pull code from remote Git repository
- Network connection is unstable
- User wants to automatically handle Git operation failures
- User requests to retry Git operations until successful

## How to Execute

1. **Determine Operation**: Identify if user needs push or pull
2. **Run Operation Loop**:
   - Display operation start message
   - Execute Git command
   - Check exit code
   - If successful: Display success message and exit
   - If failed: Display failure message and wait 5 seconds before retrying

## Implementation Code

### For Git Push

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

### For Git Pull

```powershell
while ($true) {
    Write-Host '尝试拉取...' -ForegroundColor Green
    git pull
    if ($LASTEXITCODE -eq 0) {
        Write-Host '拉取成功！' -ForegroundColor Green
        break
    } else {
        Write-Host '拉取失败，5秒后重试...' -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
}
```

## What to Expect

- **Push Success**: Green "推送成功！" message and process completes
- **Push Failure**: Red "推送失败，5秒后重试..." message and retry after 5 seconds
- **Pull Success**: Green "拉取成功！" message and process completes
- **Pull Failure**: Red "拉取失败，5秒后重试..." message and retry after 5 seconds
- **Continues**: Runs until operation succeeds or user interrupts

## Notes

- This skill runs continuously until Git operation succeeds
- Ensure remote repository is properly configured
- For push: Ensure there are commits to push
- For pull: Ensure local repository is ready to pull
- Network stability may affect execution time