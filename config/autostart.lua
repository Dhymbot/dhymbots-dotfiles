-- Auto-start config
-- if you dont use UWSM add your auto start programs here, otherwise use XDG autostart https://wiki.archlinux.org/title/XDG_Autostart

hl.on("hyprland.start", function ()
    hl.exec_cmd("dbus-update-activation-environment --systemd --all")
    hl.exec_cmd("noctalia")
    hl.exec_cmd("xhost +SI:localuser:root")
    hl.exec_cmd("xava")
    hl.exec_cmd("xava -p ~/.config/xava/config2")
    hl.exec_cmd("discord")
    hl.exec_cmd("handy --start-hidden")
    hl.exec_cmd("~/.config/hypr/scripts/perujarvis.sh")
end)
