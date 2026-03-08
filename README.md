When scheduler-related code is updated on the VPS:

```bash
cd ~/apps/brief-agent
git pull
sudo systemctl restart daily-brief-agent.service
sudo systemctl status daily-brief-agent.service
```

If only normal imported Python files are changed, restart is enough.
If the `.service^ file itself is changed, then do:

```bash
sudo systemctl daemon-reload
sudo systemctl restart daily-brief-agent.service
```
