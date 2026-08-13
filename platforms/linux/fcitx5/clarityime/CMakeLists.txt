add_library(clarityime SHARED clarityime.cpp)

target_link_libraries(clarityime Fcitx5::Core)
target_include_directories(clarityime PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

set_target_properties(clarityime PROPERTIES PREFIX "" OUTPUT_NAME "clarityime")

install(TARGETS clarityime DESTINATION "${FCITX_INSTALL_LIBDIR}/fcitx5")

install(FILES clarityime.conf
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon")

install(FILES clarityime.input.conf
        DESTINATION "${FCITX_INSTALL_PKGDATADIR}/inputmethod"
        RENAME clarityime.conf)

install(FILES engine.py
        DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/clarityime/fcitx5")
