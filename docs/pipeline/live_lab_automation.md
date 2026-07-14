# Live Lab Automation

## Goal

The live lab should not require retyping every Docker, Suricata, Wazuh polling,
and OPC UA monitor command. The repeatable startup flow is now wrapped in small
scripts so the operator can start, inspect, and stop the platform consistently.

The scripts automate the platform services, but they do not remove the OT lab
assumptions:

- KEPServerEX must still be installed, configured, and exposing OPC UA on Windows.
- UaExpert is still the manual engineering/operator action used for the live test.
- Wazuh rules and agent collection must still be deployed correctly.
- Real credentials must stay in `.env`, never in committed scripts.

## Windows Host Startup

From the repository root on Windows:

```powershell
.\scripts\start-live-platform.ps1
```

This starts:

- PostgreSQL 18
- Django backend
- Next.js frontend
- Wazuh poller profile
- Suricata flow proof script

It also checks:

- KEPServerEX OPC UA port reachability
- backend health endpoint
- frontend reachability

Use this if you want to start Docker only:

```powershell
.\scripts\start-live-platform.ps1 -SkipSuricata
```

Use this if the Wazuh Indexer credentials are not configured yet:

```powershell
.\scripts\start-live-platform.ps1 -SkipPoller
```

## Optional Ubuntu Monitor Over SSH

If Windows can SSH into the Ubuntu VM, the same script can start the OPC UA
monitor remotely.

Set these environment variables on Windows:

```powershell
$env:LAB_UBUNTU_HOST = "192.168.56.10"
$env:LAB_UBUNTU_USER = "ahmed_bahaa"
$env:LAB_UBUNTU_OPCUA_CLIENT_DIR = "~/ot-project/opcua-client"
```

Then run:

```powershell
.\scripts\start-live-platform.ps1 -StartUbuntuMonitor
```

If you use an SSH key:

```powershell
$env:LAB_UBUNTU_SSH_KEY = "C:\Users\Ahmed_364\.ssh\id_ed25519"
.\scripts\start-live-platform.ps1 -StartUbuntuMonitor
```

The remote monitor command runs:

```bash
bash ../scripts/start-ubuntu-monitor.sh
```

It writes monitor output to:

```text
opcua-client/logs/opcua_monitor_automation.out
```

## Ubuntu Environment File

The Python OPC UA monitor runs on Ubuntu and reads:

```text
opcua-client/.env
```

Create it on Ubuntu from the repository root:

```bash
cp opcua-client/.env.example opcua-client/.env
nano opcua-client/.env
```

Set the lab values there:

```text
OPCUA_ENDPOINT=opc.tcp://192.168.56.1:49320
OPCUA_USERNAME=<KEPSERVER_USERNAME>
OPCUA_PASSWORD=<KEPSERVER_PASSWORD>
```

Do not commit `opcua-client/.env`. It is ignored by Git.

## Ubuntu Monitor Automation

Run these from the repository root on Ubuntu, meaning the directory that contains
both `scripts/` and `opcua-client/`.

Start the monitor in the background:

```bash
bash scripts/start-ubuntu-monitor.sh
```

Check monitor status and recent logs:

```bash
bash scripts/status-ubuntu-monitor.sh
```

Stop the monitor:

```bash
bash scripts/stop-ubuntu-monitor.sh
```

The start script subscribes to all simulator tags and writes:

```text
opcua-client/logs/opcua_monitor_automation.out
opcua-client/logs/opcua_monitor.pid
```

## Ubuntu Foreground Monitor Fallback

If you want the monitor attached to the terminal for debugging:

```bash
bash scripts/run-opcua-trigger-pipeline.sh
```

The script is repo-relative and supports overrides:

```bash
OPCUA_MONITOR_SCENARIO_ID="uaexpert-live-test" \
OPCUA_MONITOR_INTERVAL_MS=1000 \
bash scripts/run-opcua-trigger-pipeline.sh
```

## Status

From Windows:

```powershell
.\scripts\status-live-platform.ps1
```

This prints:

- Docker Compose service state
- backend and frontend reachability
- KEPServerEX port reachability
- Suricata process and `eve.json` status
- recent Wazuh poller logs

## Stop

Stop Docker services:

```powershell
.\scripts\stop-live-platform.ps1
```

Stop Docker and Suricata:

```powershell
.\scripts\stop-live-platform.ps1 -StopSuricata
```

Stop Docker, Suricata, and the SSH-started Ubuntu monitor:

```powershell
.\scripts\stop-live-platform.ps1 -StopSuricata -StopUbuntuMonitor
```

## Live Test After Automation

After startup, the only live operator step should be:

```text
Change a monitored tag in UaExpert.
```

Monitored tags:

```text
DEBI
MOTOR1
MOTOR2
SAMANDIRA
SU_SEVIYESI
ScenarioID
VALF
```

Expected path:

```text
UaExpert tag change
-> OPC UA monitor JSONL
-> Wazuh process/tag rule
-> Suricata OPC UA flow
-> Wazuh rule 110104
-> Wazuh poller
-> Django live alert
-> backend case correlation
-> frontend dashboard
```
