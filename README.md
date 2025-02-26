# 🎯 SWATCH (Slurm Watch)

A sleek, modern job monitoring tool for Slurm workload manager that doesn't make you want to pull your hair out! 

![SWATCH GUI](./Swatch_gui_readme.png)

## 🌟 Features

- 🎨 Beautiful dark theme interface
- 🔄 Real-time job status monitoring
- 🔐 Secure SSH authentication
- 🎯 Status-based color coding
- ⚡ Configurable auto-refresh
- 🎮 Drag-and-drop window movement
- 🧪 Test mode for demos and development

## 📦 Installation

### Using pip

```bash
pip install swatch-slurm
```

### Development Installation
```bash
git clone https://github.com/Jakeelamb/SWATCH.git
cd SWATCH
pip install -e ".[dev]"
```

## 🚀 Usage

After installation, simply run the tool using the `swatch` command:

```bash
# Run SWATCH with normal mode
swatch

# Run SWATCH in test mode
swatch --test
```

## 🎮 Command Line Options

| Flag | Description | Example |
|------|-------------|---------|
| `-h, --help` | Show help message and exit | `swatch --help` |
| `-t, --test` | Run in test mode with sample data | `swatch --test` |

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

## 🐛 Known Issues


Remember: Happy monitoring! 🚀
