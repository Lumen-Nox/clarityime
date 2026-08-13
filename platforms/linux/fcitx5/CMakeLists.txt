cmake_minimum_required(VERSION 3.16)
project(fcitx5-clarityime VERSION 0.3.0 LANGUAGES CXX)

find_package(Fcitx5Core REQUIRED)

include("${FCITX_INSTALL_CMAKECONFIG_DIR}/Fcitx5Utils/Fcitx5CompilerSettings.cmake")

add_subdirectory(clarityime)
