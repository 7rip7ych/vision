import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "controls" as MyControls

ApplicationWindow {
    id: appWindow
    visible: true
    width: 800
    height: 500
    title: "Vision"
    property QtObject backend
    Rectangle {
        anchors.fill: parent
        color: "#eee"

        Image {
            source: "./images/logo/draft1.2_vision_logo_thicker.ico"
            anchors {
                top: parent.top
                left: parent.left
                margins: 5
            }
            fillMode: Image.PreserveAspectFit
            width: 80
            height: 80
        }

        ColumnLayout {
            width: parent.width
            height: parent.height
            spacing: 10

            Rectangle {
                Layout.fillWidth: true
                height: 70
                color: "transparent"

                Text {
                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        bottom: parent.bottom
                    }
                    text: "Data Visualiser"
                    font.pixelSize: 48
                    color: "#000"
                    font.family: "Eras ITC"
                    font.bold: true
                }
            }

            Image {
                Layout.fillWidth: true
                Layout.fillHeight: true
                source: "./images/lines.svg"
                fillMode: Image.Stretch
                opacity: 0.75
            }


            ColumnLayout {
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 10
                spacing: 2


                MyControls.CheckBox {
                    Layout.alignment: Qt.AlignHCenter
                    id: getFull
                    text: qsTr("Get full data")
                    height: 15
                    width: 15
                }

                MyControls.Button {
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignHCenter
                    padding: 15
                    horizontalPadding: 40
                    text: "Upload files"
                    onClicked: {
                        if (getFull.checkState == Qt.Checked)
                            backend.input_files_all()
                        else
                            backend.input_files()
                    }
                }

            }


            RowLayout {
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter
                spacing: 50

                MyControls.Button {
                    Layout.fillHeight: true
                    implicitWidth: 150
                    text: "Open table"

                    MouseArea {
                        cursorShape: Qt.PointingHandCursor
                        anchors.fill: parent
                        onClicked: {
                            backend.open_analyzer()
                        }
                    }

                }

                MyControls.Button {
                    Layout.fillHeight: true
                    implicitWidth: 150
                    text: "Open analysis"

                    MouseArea {
                        cursorShape: Qt.PointingHandCursor
                        anchors.fill: parent
                        onClicked: {
                            backend.open_analyzer()
                        }
                    }
                }
            }
            

            MyControls.Button {
                text: "Quit"
                Layout.alignment: Qt.AlignRight
                padding: 2
                MouseArea {
                    cursorShape: Qt.PointingHandCursor
                    anchors.fill: parent
                    onClicked: {
                        backend.off()
                    }
                }
            }
        }
    }
}