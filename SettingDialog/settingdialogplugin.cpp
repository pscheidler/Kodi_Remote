#include "settingdialog.h"
#include "settingdialogplugin.h"

#include <QtPlugin>

SettingDialogPlugin::SettingDialogPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void SettingDialogPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool SettingDialogPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *SettingDialogPlugin::createWidget(QWidget *parent)
{
    return new SettingDialog(parent);
}

QString SettingDialogPlugin::name() const
{
    return QLatin1String("SettingDialog");
}

QString SettingDialogPlugin::group() const
{
    return QLatin1String("");
}

QIcon SettingDialogPlugin::icon() const
{
    return QIcon();
}

QString SettingDialogPlugin::toolTip() const
{
    return QLatin1String("");
}

QString SettingDialogPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool SettingDialogPlugin::isContainer() const
{
    return false;
}

QString SettingDialogPlugin::domXml() const
{
    return QLatin1String("<widget class=\"SettingDialog\" name=\"settingDialog\">\n</widget>\n");
}

QString SettingDialogPlugin::includeFile() const
{
    return QLatin1String("settingdialog.h");
}
#if QT_VERSION < 0x050000
Q_EXPORT_PLUGIN2(settingdialogplugin, SettingDialogPlugin)
#endif // QT_VERSION < 0x050000
