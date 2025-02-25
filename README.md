# 🎯 SWATCH (Slurm Watch)

A sleek, modern job monitoring tool for Slurm workload manager that doesn't make you want to pull your hair out! 

![SWATCH Demo](assets/demo.gif)

## 🌟 Features

- 🎨 Beautiful dark theme interface
- 🔄 Real-time job status monitoring
- 🔐 Secure SSH authentication
- 🎯 Status-based color coding
- ⚡ Configurable auto-refresh
- 🎮 Drag-and-drop window movement
- 🧪 Test mode for demos and development

## 🚀 Quick Start

## 🎮 Command Line Options

| Flag | Description | Example |
|------|-------------|---------|
| `-t, --test` | Run in test mode with sample data | `python slurm_watch.py --test` |

## 🎯 Job Status Colors

| Status | Color | Description |
|--------|-------|-------------|
| 🟢 Running | Soft Green | Job is actively running |
| 🟡 Pending | Soft Orange | Job is waiting in queue |
| 🔵 Completed | Soft Blue | Job finished successfully |
| 🔴 Failed | Soft Red | Job failed or timed out |

## ⚙️ Configuration

SWATCH automatically saves your configuration in `~/.hpcjobmonitor/config.json`. You can:

- 💾 Save login credentials (optional)
- ⏰ Set refresh intervals:
  - 5 seconds
  - 30 seconds
  - 1 minute
  - 5 minutes
  - 10 minutes
  - 30 minutes

## 🔒 Security Note

When saving credentials, passwords are stored locally. For enhanced security:
- 🚫 Don't save credentials on shared machines
- ✅ Use SSH keys when possible
- 🔑 Ensure `~/.hpcjobmonitor` has appropriate permissions

## 🎨 Interface Features

- 🖱️ Draggable window (click and drag title bar)
- 📊 Sortable job columns
- 🎯 Status indicators
- 📈 Job statistics summary
- ⏱️ Auto-refresh toggle

## 🤝 Contributing

Found a bug? Want to add a feature? We'd love your help! 

1. 🍴 Fork the repository
2. 🌿 Create your feature branch
3. 💾 Commit your changes
4. 📤 Push to the branch
5. 🎯 Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Fun Facts

- The name "SWATCH" comes from "Slurm Watch" (not the watch company! 😉)
- The color scheme was inspired by modern code editors
- It's probably the most stylish Slurm monitor you'll ever use! 🎨

## 🐛 Known Issues

- May cause increased productivity
- Might make other monitoring tools look boring
- Could lead to excessive job submission due to how fun it is to watch them run

Remember: Happy monitoring! 🚀
