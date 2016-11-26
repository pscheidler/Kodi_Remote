CONFIG      += plugin debug_and_release
TARGET      = $$qtLibraryTarget(settingdialogplugin)
TEMPLATE    = lib

HEADERS     = settingdialogplugin.h
SOURCES     = settingdialogplugin.cpp
RESOURCES   = icons.qrc
LIBS        += -L. 

greaterThan(QT_MAJOR_VERSION, 4) {
    QT += designer
} else {
    CONFIG += designer
}

target.path = $$[QT_INSTALL_PLUGINS]/designer
INSTALLS    += target

include(settingdialog.pri)

FORMS += \
    dialog2.ui
