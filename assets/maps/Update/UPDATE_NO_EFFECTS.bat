@echo off
copy "..\tags.dat" "bak\tags.dat"
copy "..\string_ids.dat" "bak\string_ids.dat"
copy "..\resources.dat" "bak\resources.dat"
copy "..\tag_list.csv" "bak\tag_list.csv"
Type DXVK_MENU_NO_EFFECTS.cmds | "TagTool.exe" ../tags.dat