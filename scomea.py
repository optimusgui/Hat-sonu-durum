from PyQt5.QtWidgets import QGraphicsDropShadowEffect
import stylesheet_variables as style_vars
from PyQt5.QtCore import QDateTime
import sqlite3
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMenu, QDialog, QLabel, QPushButton, QVBoxLayout, QMessageBox, QStackedWidget
import time
from ui_MainWindow import Ui_MainWindow
from ui_SplashWindow import *
from CustomWidgetClasses import *
import snap7
import pymssql
from snap7.util import *
import math

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)

        self.anapencere = Ui_MainWindow()
        self.anapencere.setupUi(self)

        self.anapencere.pushButtonSwitchTopageMain.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageMakine.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageMakineParametreSecim.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageParametreEkle.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageAyarlar.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageLog.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageFirma.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageFirmaListele.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageFirmaEkle.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageMakineListele.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageMakineEkle.clicked.connect(self.switchToOtherMainPage)
        self.anapencere.pushButtonSwitchTopageMakineParametre.clicked.connect(self.switchToOtherMainPage)
        # self.anapencere.pushButtonYaziciDetails.clicked.connect(self.printerDetailsShow)
        self.anapencere.pushButtonOpenLoginMenu.clicked.connect(self.loginMenuOpenClose)
        self.anapencere.pushButtonGirisYap.clicked.connect(self.girisYapButon)
        self.anapencere.pushButtonCikisYap.clicked.connect(self.cikisYapButon)
        self.anapencere.widgetSagAcilirMenu.setVisible(False)
        self.anapencere.pushButtonSagAcilirMenuKapat.clicked.connect(self.widgetSagAcilirMenuKapatButon)
        self.anapencere.pushButtonFirmaEkle.clicked.connect(self.FirmaKayit)
        self.anapencere.pushButtonMakineEkleIleri.clicked.connect(self.FirmaIleri)
        self.anapencere.pushButtonMakineEkle.clicked.connect(self.MakineEkle)
        self.anapencere.pushButtonYeniMakineEkle.clicked.connect(self.YeniMakineEkle)
        self.anapencere.pushButtonParametreIleri.clicked.connect(self.MakineIleri)
        self.anapencere.pushButtonParametreEkle.clicked.connect(self.ParametreEkle)
        self.anapencere.pushButtonFirmaGuncelle.clicked.connect(self.guncelleFirma)
        self.anapencere.pushButtonFirmaListeleGeri.clicked.connect(self.firmaListeleGeriGel)
        self.anapencere.pushButtonMakineParametreKaydet.clicked.connect(self.makineParametreKaydet)

        self.anapencere.comboBoxParametreFirmaAdi.currentIndexChanged.connect(self.makineBilgisi)
        self.anapencere.comboBoxParametreMakineAdi.currentIndexChanged.connect(self.parametreMakineOzellik)
        self.anapencere.pushButtonDataGetir.clicked.connect(self.deneme)

        self.anapencere.pageAyarlar.setEnabled(False)

        self.yeni_log_durumu = False
        self.local_db = None
        self.plc_istek_list = []
        self.plc_istek_list_1 = []

        self.PLC = snap7.client.Client()
        self.PLCConnectionStatus = False

        self.PLC_ReadTimer = QtCore.QTimer()
        self.PLC_ReadTimer.timeout.connect(self.PLC_OkumaYazmaDongu)  # okuma yazma dongu
        self.PLC_ReadTimer.setInterval(300)

        self.PLCReconnectionTimer = QtCore.QTimer()
        self.PLCReconnectionTimer.setInterval(300)
        self.PLCReconnectionTimer.timeout.connect(self.PLC_Connect)  # plc baglanti
        self.LOKAL_DATABASE_CONNECTION_STATUS = False

        self.PLC_GELEN_SINYAL_LIST_OLD =[False, False, False, False, False, False, False,False, False]

        #PROGRESS-BAR OPTIMUS
        self.RadioButtonTimer = QtCore.QTimer()
        self.RadioButtonTimer.timeout.connect(self.statusShow)
        self.RadioButtonTimer.setInterval(30)
        self.statusVariable = 0
        self.RadioButtonTimer.start()
        self.firmaGuncelle_id = 0

        self.yazicilariKontrolThread = None
        QtCore.QTimer.singleShot(100, lambda: self.baslangicFonksiyonlariniCagir())

    def baslangicFonksiyonlariniCagir(self):
        try:
            self.baglantiAyarlariniYukle()
            self.PLC_Connect()
            self.MssqlBaglan()
            pass

        except Exception as e:
            self.log_yaz("BAŞLANGIÇ FONKSİYONLARINI ÇAĞIR", str(e))
            pass


    def PLC_Connect(self):
        try:
            if self.PLC_ReadTimer.isActive():
                self.PLC_ReadTimer.stop()

            if self.PLC.get_connected():
                self.PLC.destroy()
                self.PLC = snap7.client.Client()

            PLC_IP = self.PLC_IP
            self.PLC.connect(PLC_IP, 0, 0)
            self.PLCConnectionStatus = self.PLC.get_connected()
            if self.PLCConnectionStatus:
                self.anapencere.labelPLCConnectionStatus.setStyleSheet(style_vars.stylesheet_green)
                self.anapencere.labelPLCConnectionStatus.setText("PLC")
                if not self.PLC_ReadTimer.isActive():
                    self.PLC_ReadTimer.start()
                    pass
                if self.PLCReconnectionTimer.isActive():
                    self.PLCReconnectionTimer.stop()
            else:
                self.anapencere.labelPLCConnectionStatus.setStyleSheet(style_vars.stylesheet_red)
                self.anapencere.labelPLCConnectionStatus.setText("PLC")

                time.sleep(0.1)
                pass
            return self.PLCConnectionStatus

        except Exception as e:
            self.anapencere.labelPLCConnectionStatus.setStyleSheet(style_vars.stylesheet_red)
            self.anapencere.labelPLCConnectionStatus.setText("PLC")
            self.log_yaz("PLC BAGLANTI HATASI", str(e))
            if not self.PLCReconnectionTimer.isActive():
                self.PLCReconnectionTimer.start()
            return False
            pass

    def PLC_OkumaYazmaDongu(self):
        try:
            if self.PLCConnectionStatus:
                plc_sinyal_area_data = self.PLC.read_area(snap7.types.Areas.DB, 28, 0, 8)

                self.plcSinyalleriGoster(plc_sinyal_area_data)
                #self.dataGetir(plc_sinyal_area_data)

        except Exception as e:
            self.anapencere.labelAyarlarLog.setText("PLC OKUMA HATASI")
            if not self.PLCReconnectionTimer.isActive():
                self.PLCReconnectionTimer.start()
            pass

    def plcSinyalleriGoster(self):
        try:
            pass
            #self.anapencere.labelDeneme1.setText(str(get_bool(plc_sinyal_area_data, 0, 0)))
            #self.anapencere.labelDeneme2.setText(str(get_int(plc_sinyal_area_data, 2)))
        except Exception as e:
            self.anapencere.labelAyarlarLog.setText("SINYALLERI GOSTERME HATADA")

    def dataGetir(self, plc_sinyal_area_data):
        try:
            makineAd = self.anapencere.comboBoxParametreMakineAdi.currentText()
            self.database_cursor.execute(f"SELECT Makine_Id FROM Makine_Tbl WHERE Makine_Ad = '{makineAd}'")
            gelen_data = self.database_cursor.fetchone()
            if gelen_data:
                makine_idx = gelen_data[0]
                self.database_cursor.execute(
                    f"SELECT DISTINCT PLC_DB FROM Makine_Parametre_Tbl WHERE Makine_Idx = '{makine_idx}'")
                db_bilgisi = self.database_cursor.fetchall()  # Tüm benzersiz PLC_DB değerlerini al
                if db_bilgisi:
                    for db in db_bilgisi:
                        print(db[0])
                        plc_sinyal_area_data = self.PLC.read_area(snap7.types.Areas.DB, db[0], 0, 8)
                        self.database_cursor.execute(f"""
                            SELECT Parametre_Tbl.Veri_Tipi, Makine_Parametre_Tbl.Offset_No
                            FROM Makine_Parametre_Tbl
                            INNER JOIN Parametre_Tbl
                            ON Makine_Parametre_Tbl.Parametre_Idx = Parametre_Tbl.Parametre_Id
                            WHERE Makine_Parametre_Tbl.Makine_Idx = '{makine_idx}'
                            AND Makine_Parametre_Tbl.PLC_DB = '{db[0]}'
                        """)
                        offset_bilgisi = self.database_cursor.fetchall()
                        if offset_bilgisi:
                            for offset in offset_bilgisi:
                                print(offset[0], offset[1])
                                if offset[0] == "Int":
                                    offset_no = int(offset[1])  # float'ı int'e dönüştür
                                    print(" DENEME ", str(get_bool(plc_sinyal_area_data, offset_no, 0)))

                        print("bd bilgisi son")
                else:
                    self.log_yaz("DATA BİLGİSİ GETİRME HATADA :", "DB BULUNAMADI")
        except Exception as e:
            self.log_yaz("DATA GETİR HATADA :", str(e))

    def ayir_float(self, float_sayi):
        ondalik_kisim, tam_sayi_kisim = math.modf(float_sayi)
        ondalik_kisim = int(ondalik_kisim * 10)
        return int(tam_sayi_kisim), ondalik_kisim

    def deneme(self):
        try:
            python_date = QDateTime.currentDateTime().toPyDateTime()
            tarih = python_date.strftime("%d-%m-%Y %H:%M:%S")
            makineAd = self.anapencere.comboBoxParametreMakineAdi.currentText()
            self.database_cursor.execute(f"SELECT Makine_Id FROM Makine_Tbl WHERE Makine_Ad = '{makineAd}'")
            gelen_data = self.database_cursor.fetchone()
            if gelen_data:
                makine_idx = gelen_data[0]
                self.database_cursor.execute(
                    f"SELECT DISTINCT PLC_DB FROM Makine_Parametre_Tbl WHERE Makine_Idx = '{makine_idx}'")
                db_bilgisi = self.database_cursor.fetchall()  # Tüm benzersiz PLC_DB değerlerini al
                if db_bilgisi:
                    for db in db_bilgisi:
                        print(db[0])
                        # Maksimum offset değeri ve okuma boyutunu belirle
                        self.database_cursor.execute(f"""
                                SELECT MAX(Offset_No) 
                                FROM Makine_Parametre_Tbl 
                                WHERE Makine_Idx = '{makine_idx}' AND PLC_DB = '{db[0]}'
                            """)
                        max_offset = self.database_cursor.fetchone()
                        self.database_cursor.execute(f"Select Parametre_Idx from Makine_Parametre_Tbl Where Makine_Idx = '{makine_idx}' AND PLC_DB = '{db[0]}' AND OFFSET_NO='{max_offset[0]}'")
                        Parametre_Idx = self.database_cursor.fetchone()
                        self.database_cursor.execute(f"Select Veri_Tipi From Parametre_Tbl Where Parametre_Id ='{Parametre_Idx[0]}'")
                        Veri_Tipi = self.database_cursor.fetchone()
                        if max_offset and max_offset[0] is not None:
                            if Veri_Tipi[0] == "Int":
                                read_size = int(max_offset[0]) + 2  # Okuma boyutunu belirle, ihtiyaç durumuna göre ayarla
                                print(f"Okunan DB {db[0]} boyutu {read_size}")
                            elif Veri_Tipi[0] == "Bool":
                                read_size = int(max_offset[0]) + 1  # Okuma boyutunu belirle, ihtiyaç durumuna göre ayarla
                                print(f"Okunan DB {db[0]} boyutu {read_size}")
                            elif Veri_Tipi[0] == "DINT":
                                read_size = int(max_offset[0]) + 4  # Okuma boyutunu belirle, ihtiyaç durumuna göre ayarla
                                print(f"Okunan DB {db[0]} boyutu {read_size}")
                            else:
                                read_size = 10
                            try:
                                plc_sinyal_area_data = self.PLC.read_area(snap7.types.Areas.DB, db[0], 0, read_size)
                            except Exception as e:
                                self.log_yaz("PLC READ ERROR: ", str(e))
                                continue

                            self.database_cursor.execute(f"""
                                    SELECT Parametre_Tbl.Veri_Tipi, Makine_Parametre_Tbl.Offset_No, Makine_Parametre_Tbl.Makine_Parametre_Id
                                    FROM Makine_Parametre_Tbl
                                    INNER JOIN Parametre_Tbl
                                    ON Makine_Parametre_Tbl.Parametre_Idx = Parametre_Tbl.Parametre_Id
                                    WHERE Makine_Parametre_Tbl.Makine_Idx = '{makine_idx}'
                                    AND Makine_Parametre_Tbl.PLC_DB = '{db[0]}'
                                """)
                            offset_bilgisi = self.database_cursor.fetchall()
                            if offset_bilgisi:
                                for offset in offset_bilgisi:
                                    print(offset[0], offset[1])
                                    if offset[0] == "Int":
                                        offset_no = int(offset[1])  # float'ı int'e dönüştür
                                        try:
                                            self.value = get_int(plc_sinyal_area_data, offset_no)
                                            print(" DENEME ", str(self.value))
                                            self.database_cursor.execute(
                                                f"UPDATE Makine_Parametre_Tbl SET Tarih = '{tarih}', Deger = '{self.value}' Where Makine_Idx = '{makine_idx}' AND Makine_Parametre_Id = '{offset[2]}'")
                                            self.local_db.commit()
                                        except Exception as e:
                                            self.log_yaz("GET INT Hata: ", str(e))
                                    elif offset[0] == "DINT":
                                        offset_no = int(offset[1])  # float'ı int'e dönüştür
                                        try:
                                            self.value = get_dint(plc_sinyal_area_data, offset_no)
                                            print(" DENEME ", str(self.value))
                                            self.database_cursor.execute(
                                                f"UPDATE Makine_Parametre_Tbl SET Tarih = '{tarih}', Deger = '{self.value}' Where Makine_Idx = '{makine_idx}' AND Makine_Parametre_Id = '{offset[2]}'")
                                            self.local_db.commit()
                                        except Exception as e:
                                            self.log_yaz("GET DINT Hata: ", str(e))
                                    elif offset[0] == "Bool":
                                        offset_no = float(offset[1])  # float'ı int'e dönüştür
                                        print("Bool Offset no = ", str(offset_no))
                                        tam_sayi, ondalik_sayi = self.ayir_float(offset_no)
                                        print("Tam sayı : ", tam_sayi, "ondalık sayı :", ondalik_sayi)
                                        try:
                                            self.value = get_bool(plc_sinyal_area_data, tam_sayi, ondalik_sayi)
                                            print(" DENEME ", str(self.value))
                                            self.database_cursor.execute(
                                                f"UPDATE Makine_Parametre_Tbl SET Tarih = '{tarih}', Deger = '{self.value}' Where Makine_Idx = '{makine_idx}' AND Makine_Parametre_Id = '{offset[2]}'")
                                            self.local_db.commit()
                                        except Exception as e:
                                            self.log_yaz("GET DINT Hata: ", str(e))
                                    else:
                                        self.value = 0
                                        self.database_cursor.execute(
                                            f"UPDATE Makine_Parametre_Tbl SET Tarih = '{tarih}', Deger = '{self.value}' Where Makine_Idx = '{makine_idx}' AND Makine_Parametre_Id = '{Parametre_Idx[0]}'")
                                        self.local_db.commit()
                            print("bd bilgisi son")
                        else:
                            self.log_yaz("OFFSET BİLGİSİ GETİRME HATASI: ", "MAKSIMUM OFFSET BULUNAMADI")
                else:
                    self.log_yaz("DATA BİLGİSİ GETİRME HATASI: ", "DB BULUNAMADI")
        except Exception as e:
            self.log_yaz("DATA GETİR HATASI: ", str(e))

    def MssqlBaglan(self):
        try:
            self.local_db = pymssql.connect(server=self.DB_SERVER,
                                            database=self.DB_VERITABANI,
                                            user=self.DB_USERNAME,
                                            password=self.DB_PASSWORD)
            self.database_cursor = self.local_db.cursor()
            self.anapencere.labelMssqlConnectionStatus.setText("MSSQL")
            self.anapencere.labelMssqlConnectionStatus.setStyleSheet(style_vars.stylesheet_green)
        except Exception as e:
            self.anapencere.labelAyarlarLog.setText("MSSQL BAĞLANMA HATADA : ", str(e))

    def FirmaKayit(self):
        try:
            python_date = QDateTime.currentDateTime().toPyDateTime()
            tarih = python_date.strftime("%d-%m-%Y %H:%M:%S")
            FirmaAdi = self.anapencere.lineEditFirmaAdi.text()
            Aciklama = self.anapencere.lineEditAciklama.text()
            PcIp = self.anapencere.lineEditPcIp.text()
            SecomeaNickname = self.anapencere.lineEditSecomeaNickname.text()
            SecomeaKopru = self.anapencere.lineEditSecomeaKopru.text()

            self.database_cursor.execute(
                f"INSERT INTO Firma_Tbl(Firma_Ad,Aciklama,Kayit_Yapan, Kayit_Tarihi, PC_IP, Secomea_Nickname,Secomea_DEV1) VALUES ('{FirmaAdi}','{Aciklama}','optimak','{tarih}','{PcIp}','{SecomeaNickname}','{SecomeaKopru}')")
            self.local_db.commit()
            self.anapencere.FirmaEkleLog.setText("FİRMA EKLENDİ")

            self.anapencere.lineEditFirmaAdi.setEnabled(False)
            self.anapencere.lineEditAciklama.setEnabled(False)
            self.anapencere.lineEditPcIp.setEnabled(False)
            self.anapencere.lineEditSecomeaNickname.setEnabled(False)
            self.anapencere.lineEditSecomeaKopru.setEnabled(False)

        except Exception as e:
            self.anapencere.FirmaEkleLog.setText("FİRMA EKLENEMEDİ : ", str(e))

    def FirmaIleri(self):
        try:

            firmaAdi = self.anapencere.lineEditFirmaAdi.text()
            self.anapencere.comboBoxFirmaAdi.addItem(firmaAdi)
            self.anapencere.pushButtonSwitchTopageMakine.click()
            self.anapencere.pushButtonSwitchTopageMakineEkle.click()
        except Exception as e:
            self.log_yaz("FİRMA İLERİ BUTON HATADA ", str(e))

    def MakineEkle(self):
        try:
            firmaAdi = self.anapencere.comboBoxFirmaAdi.currentText()
            self.database_cursor.execute(f"SELECT Firma_Id from Firma_Tbl Where Firma_ad = '{firmaAdi}'")
            firmaBilgi = self.database_cursor.fetchone()
            if firmaBilgi:
                firmaId = int(firmaBilgi[0])
                makineAd = self.anapencere.lineEditMakineAdi.text()
                makinePlcIp = self.anapencere.lineEditMakinePlcIp.text()
                self.database_cursor.execute(f"INSERT INTO Makine_Tbl(Makine_Ad,Makine_IP,Firma_Idx) Values ('{makineAd}','{makinePlcIp}','{firmaId}')")
                self.local_db.commit()
                self.anapencere.labelSayfaAltiLog.setText("MAKİNE EKLENDİ.")
            else:
                self.log_yaz("FIRMA BİLGİSİ SEÇİLİ DEĞİL FİRMA SEÇİNİZ.", " ")

            self.anapencere.lineEditMakineAdi.setEnabled(False)
            self.anapencere.lineEditMakinePlcIp.setEnabled(False)

        except Exception as e:
            self.log_yaz("MAKİNE EKLEME HATADA : ", str(e))

    def MakineIleri(self):
        try:
            firmaAdi = self.anapencere.comboBoxFirmaAdi.currentText()
            makineAdi = self.anapencere.lineEditMakineAdi.text()
            self.anapencere.comboBoxParametreSecimFirmaAdi.addItem(firmaAdi)
            self.anapencere.comboBoxParametreSecimMakineAdi.addItem(makineAdi)
            self.anapencere.pushButtonSwitchTopageMakineParametreSecim.click()

        except Exception as e:
            self.log_yaz("MAKİNE ILERI BUTTON HATADA :", str(e))

    def YeniMakineEkle(self):
        try:
            self.anapencere.lineEditMakineAdi.setText("")
            self.anapencere.lineEditMakinePlcIp.setText("")
            self.anapencere.lineEditMakineAdi.setEnabled(True)
            self.anapencere.lineEditMakinePlcIp.setEnabled(True)

        except Exception as e:
            self.log_yaz("Yeni Makine Ekleme Hatada :", str(e))

    def ParametreEkle(self):
        try:
            parametreAdi = self.anapencere.lineEditParametreAdi.text()
            parametreTip = self.anapencere.comboBoxParametreTip.currentText()
            parametreVeriTipi = self.anapencere.comboBoxParametreVeriTipi.currentText()
            parametreOffsetNo = self.anapencere.lineEditParametreOffsetNo.text()
            parametreKonusu = self.anapencere.comboBoxParametreKonusu.currentText()
            parametreHedef = 1 if self.anapencere.checkBoxHedef.isChecked() else 0
            self.database_cursor.execute(
                f"INSERT INTO Parametre_Tbl(Parametre_Ad,Tip,Veri_Tipi, Offset_No, Konusu, Hedef) VALUES ('{parametreAdi}','{parametreTip}','{parametreVeriTipi}','{parametreOffsetNo}','{parametreKonusu}','{parametreHedef}')")
            self.local_db.commit()
            self.anapencere.labelParametreBilgi.setText("PARAMETRE EKLENDİ")
            self.anapencere.lineEditParametreAdi.setText("")

        except Exception as e:
            self.log_yaz("Parametre Ekleme Hatada : ", str(e))

    def FirmaYenile(self):
        try:
            self.database_cursor.execute(f"SELECT Firma_Id, Firma_Ad, Kayit_Yapan, Kayit_Tarihi,PC_IP FROM Firma_Tbl")
            gelen_data = self.database_cursor.fetchall()
            i = 1
            self.anapencere.tableWidgetFirmaTablo.setRowCount(0)
            self.anapencere.tableWidgetFirmaTablo.setSortingEnabled(False)

            if len(gelen_data) > 0:
                for data in gelen_data:
                    rowPosition = self.anapencere.tableWidgetFirmaTablo.rowCount()
                    self.anapencere.tableWidgetFirmaTablo.insertRow(rowPosition)

                    item = QtWidgets.QTableWidgetItem(str(i))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setVerticalHeaderItem(rowPosition, item)

                    item = QtWidgets.QTableWidgetItem()
                    item.setData(Qt.DisplayRole, (str(data[0])))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 0, item)

                    item = QtWidgets.QTableWidgetItem(str(data[1]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 1, item)

                    item = QtWidgets.QTableWidgetItem(str(data[2]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 2, item)

                    item = QtWidgets.QTableWidgetItem(str(data[3]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 3, item)

                    item = QtWidgets.QTableWidgetItem(str(data[4]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 4, item)

                    button1 = QtWidgets.QPushButton("GÜNCELLE")
                    button1.setStyleSheet(style_vars.buttons_guncelle)
                    button1.clicked.connect(lambda _, id =data[0]: self.firmaGuncelle(id))  # Buton1 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetFirmaTablo.setCellWidget(rowPosition, 5, button1)

                    button2 = QtWidgets.QPushButton("SİL")
                    button2.setStyleSheet(style_vars.buttons_sil)
                    button2.clicked.connect(lambda _, id=data[0]: self.firmaSil(id))  # Buton2 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetFirmaTablo.setCellWidget(rowPosition, 6, button2)

                    """item = QtWidgets.QTableWidgetItem(str(data[6]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 5, item)"""
                    i += 1
            else:
                pass
            self.anapencere.tableWidgetFirmaTablo.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.anapencere.tableWidgetFirmaTablo.setSortingEnabled(True)

        except Exception as e:
            self.log_yaz("DATABASE TABLO GÖSTERME HATASI", str(e))

    def firmaGuncelle(self, id):
        try:
            self.anapencere.pageFirmaGuncelle.setVisible(True)
            self.anapencere.pageFirmaListele.setVisible(False)
            self.database_cursor.execute(f"Select Firma_Id,Firma_Ad,Aciklama,PC_IP,Secomea_Nickname,Secomea_DEV1 from Firma_Tbl Where Firma_Id='{id}'")
            gelen_firma = self.database_cursor.fetchone()
            if len(gelen_firma) > 0:
                self.anapencere.lineEditFirmaAdiGuncelle.setText(gelen_firma[1])
                self.anapencere.lineEditAciklamaGuncelle.setText(gelen_firma[2])
                self.anapencere.lineEditFirmaPCIPGuncelle.setText(gelen_firma[3])
                self.anapencere.lineEditFirmaNicknameGuncelle.setText(gelen_firma[4])
                self.anapencere.lineEditFirmaKopruGuncelle.setText((gelen_firma[5]))
                self.firmaGuncelle_id = id
            else:
                self.anapencere.pageFirmaListele.setVisible(True)

        except Exception as e:
            self.log_yaz("FİRMA GÜNCELLEME SAYFA GİRİŞ HATASI")

    def guncelleFirma(self):
        try:
            if self.firmaGuncelle_id != 0:
                firmaAdi = self.anapencere.lineEditFirmaAdiGuncelle.text()
                firmaAciklama = self.anapencere.lineEditAciklamaGuncelle.text()
                firmaIP = self.anapencere.lineEditFirmaPCIPGuncelle.text()
                firmaNickname = self.anapencere.lineEditFirmaNicknameGuncelle.text()
                firmaKopru = self.anapencere.lineEditFirmaKopruGuncelle.text()
                self.database_cursor.execute(f"UPDATE Firma_Tbl Set Firma_Ad ='{firmaAdi}', Aciklama = '{firmaAciklama}', PC_IP ='{firmaIP}',Secomea_Nickname='{firmaNickname}', Secomea_DEV1 ='{firmaKopru}' Where Firma_Id ='{self.firmaGuncelle_id}'")
                self.local_db.commit()
                self.firmaGuncelle_id = 0
            else:
                self.anapencere.pageFirmaGuncelle.setVisible(False)
                self.anapencere.pageFirmaListele.setVisible(True)

            self.anapencere.pageFirmaGuncelle.setVisible(False)
            self.anapencere.pageFirmaListele.setVisible(True)
            self.FirmaYenile()
        except Exception as e:
            self.log_yaz("FİRMA GÜNCELLEME HATASI : ", str(e))

    def firmaListeleGeriGel(self):
        try:
            self.anapencere.pageFirmaGuncelle.setVisible(False)
            self.anapencere.pageFirmaListele.setVisible(True)
        except Exception as e:
            self.log_yaz("Fİrma Geri Gelmesi Hatada : ", str(e))

    def firmaSil(self, id):
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(" FİRMA SİLMEK İÇİN EMİN MİSİNİZ ?                  ")
            msgBox.setWindowTitle("SİL!")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
                self.database_cursor.execute(f"DELETE FROM Firma_Tbl Where Firma_Id ='{id}'")
                self.local_db.commit()
            else:
                pass
        except Exception as e:
            self.log_yaz("FİLMA SİL BİLGİSİ YANLIŞ!!! ", str(e))

    def MakineYenile(self):
        try:
            self.database_cursor.execute(f"select Makine_Tbl.Makine_Id, Makine_Tbl.Makine_Ad, Makine_Tbl.Makine_IP, Makine_Tbl.Firma_Idx, Firma_Tbl.Firma_Ad from Makine_Tbl Inner Join Firma_Tbl on Makine_Tbl.Firma_Idx = Firma_Tbl.Firma_Id")
            gelen_data = self.database_cursor.fetchall()
            i = 1
            self.anapencere.tableWidgetMakineListele.setRowCount(0)
            self.anapencere.tableWidgetMakineListele.setSortingEnabled(False)

            if len(gelen_data) > 0:
                for data in gelen_data:
                    rowPosition = self.anapencere.tableWidgetMakineListele.rowCount()
                    self.anapencere.tableWidgetMakineListele.insertRow(rowPosition)

                    item = QtWidgets.QTableWidgetItem(str(i))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setVerticalHeaderItem(rowPosition, item)

                    item = QtWidgets.QTableWidgetItem()
                    item.setData(Qt.DisplayRole, (str(data[0])))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setItem(rowPosition, 0, item)

                    item = QtWidgets.QTableWidgetItem(str(data[1]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setItem(rowPosition, 1, item)

                    item = QtWidgets.QTableWidgetItem(str(data[2]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setItem(rowPosition, 2, item)

                    item = QtWidgets.QTableWidgetItem(str(data[3]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setItem(rowPosition, 3, item)

                    item = QtWidgets.QTableWidgetItem(str(data[4]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineListele.setItem(rowPosition, 4, item)

                    button1 = QtWidgets.QPushButton("GÜNCELLE")
                    button1.setStyleSheet(style_vars.buttons_guncelle)
                    button1.clicked.connect(lambda _, id =data[0]: self.makineGüncelle(id))  # Buton1 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetMakineListele.setCellWidget(rowPosition, 5, button1)

                    button2 = QtWidgets.QPushButton("SİL")
                    button2.setStyleSheet(style_vars.buttons_sil)
                    button2.clicked.connect(lambda _, id=data[0]: self.makineSil(id))  # Buton2 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetMakineListele.setCellWidget(rowPosition, 6, button2)

                    """item = QtWidgets.QTableWidgetItem(str(data[6]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 5, item)"""
                    i += 1
            else:
                pass
            self.anapencere.tableWidgetMakineListele.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.anapencere.tableWidgetMakineListele.setSortingEnabled(True)

        except Exception as e:
            self.log_yaz("DATABASE TABLO GÖSTERME HATASI", str(e))

    def makineGüncelle(self, id):
        self.log_yaz("Makine Güncelleme Yapılması lazım ", str(id))

    def makineSil(self, id):
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(" MAKİNE SİLMEK İÇİN EMİN MİSİNİZ ?                  ")
            msgBox.setWindowTitle("SİL!")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
                self.database_cursor.execute(f"DELETE FROM Makine_Tbl Where Makine_Id ='{id}'")
                self.local_db.commit()
            else:
                pass
        except Exception as e:
            self.log_yaz("MAKİNA SİL BİLGİSİ YANLIŞ!!! ", str(e))

    def ParametreYenile(self):
        try:
            self.database_cursor.execute(f"Select * From Parametre_Tbl")
            gelen_data = self.database_cursor.fetchall()
            i = 1
            self.anapencere.tableWidgetParametreListele.setRowCount(0)
            self.anapencere.tableWidgetParametreListele.setSortingEnabled(False)

            if len(gelen_data) > 0:
                for data in gelen_data:
                    rowPosition = self.anapencere.tableWidgetParametreListele.rowCount()
                    self.anapencere.tableWidgetParametreListele.insertRow(rowPosition)

                    item = QtWidgets.QTableWidgetItem(str(i))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setVerticalHeaderItem(rowPosition, item)

                    item = QtWidgets.QTableWidgetItem()
                    item.setData(Qt.DisplayRole, (str(data[0])))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 0, item)

                    item = QtWidgets.QTableWidgetItem(str(data[1]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 1, item)

                    item = QtWidgets.QTableWidgetItem(str(data[2]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 2, item)

                    item = QtWidgets.QTableWidgetItem(str(data[3]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 3, item)

                    item = QtWidgets.QTableWidgetItem(str(data[4]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 4, item)

                    item = QtWidgets.QTableWidgetItem(str(data[5]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 5, item)

                    item = QtWidgets.QTableWidgetItem(str(data[6]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetParametreListele.setItem(rowPosition, 6, item)

                    button1 = QtWidgets.QPushButton("GÜNCELLE")
                    button1.setStyleSheet(style_vars.buttons_guncelle)
                    button1.clicked.connect(lambda _, id =data[0]: self.parametreGüncelle(id))  # Buton1 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetParametreListele.setCellWidget(rowPosition, 7, button1)

                    button2 = QtWidgets.QPushButton("SİL")
                    button2.setStyleSheet(style_vars.buttons_sil)
                    button2.clicked.connect(lambda _, id=data[0]: self.parametreSil(id))  # Buton2 için tıklama olayı ve ID'si
                    self.anapencere.tableWidgetParametreListele.setCellWidget(rowPosition, 8, button2)

                    """item = QtWidgets.QTableWidgetItem(str(data[6]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetFirmaTablo.setItem(rowPosition, 5, item)"""
                    i += 1
            else:
                pass
            self.anapencere.tableWidgetParametreListele.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.anapencere.tableWidgetParametreListele.setSortingEnabled(True)

        except Exception as e:
            self.log_yaz("DATABASE TABLO GÖSTERME HATASI", str(e))

    def parametreGüncelle(self, id):
        self.log_yaz("Parametre Güncelleme Hatada : ", str(id))

    def parametreSil(self, id):
        try:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(" PARAMETRE SİLMEK İÇİN EMİN MİSİNİZ ?                  ")
            msgBox.setWindowTitle("SİL!")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
                self.database_cursor.execute(f"DELETE FROM Parametre_Tbl Where Parametre_Id ='{id}'")
                self.local_db.commit()
            else:
                pass
        except Exception as e:
            self.log_yaz("MAKİNA SİL BİLGİSİ YANLIŞ!!! ", str(e))

    def makineParametreSecimYenile(self):
        try:
            self.database_cursor.execute(f"Select * From Parametre_Tbl")
            gelen_data = self.database_cursor.fetchall()
            i = 1
            self.anapencere.tableWidgetMakineParametreSecim.setRowCount(0)
            self.anapencere.tableWidgetMakineParametreSecim.setSortingEnabled(False)

            if len(gelen_data) > 0:
                for data in gelen_data:
                    rowPosition = self.anapencere.tableWidgetMakineParametreSecim.rowCount()
                    self.anapencere.tableWidgetMakineParametreSecim.insertRow(rowPosition)

                    item = QtWidgets.QTableWidgetItem(str(i))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setVerticalHeaderItem(rowPosition, item)

                    item = QtWidgets.QTableWidgetItem()
                    item.setData(Qt.DisplayRole, (str(data[0])))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 0, item)

                    item = QtWidgets.QTableWidgetItem(str(data[1]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 1, item)

                    item = QtWidgets.QTableWidgetItem(str(data[2]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 2, item)

                    item = QtWidgets.QTableWidgetItem(str(data[3]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 3, item)

                    line_edit_offset = QtWidgets.QLineEdit(str(data[4]))
                    line_edit_offset.setAlignment(QtCore.Qt.AlignCenter)
                    line_edit_offset.setStyleSheet(style_vars.stylesheet_purple)
                    self.anapencere.tableWidgetMakineParametreSecim.setCellWidget(rowPosition, 4, line_edit_offset)

                    item = QtWidgets.QTableWidgetItem(str(data[5]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 5, item)

                    item = QtWidgets.QTableWidgetItem(str(data[6]))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.anapencere.tableWidgetMakineParametreSecim.setItem(rowPosition, 6, item)

                    line_edit_db = QtWidgets.QLineEdit(str(100))
                    line_edit_db.setAlignment(QtCore.Qt.AlignCenter)
                    line_edit_db.setStyleSheet(style_vars.stylesheet_purple)
                    self.anapencere.tableWidgetMakineParametreSecim.setCellWidget(rowPosition, 7, line_edit_db)

                    checkbox_durum = QtWidgets.QCheckBox()
                    checkbox_durum.setFixedSize(60, 60)  # Boyutları ayarlama
                    checkbox_durum.setStyleSheet("QCheckBox::indicator { width: 30px; height: 30px; }")
                    checkbox_durum.stateChanged.connect(lambda state, id=data[0]: self.checkboxChanged(state, id))
                    checkbox_widget = QtWidgets.QWidget()
                    checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
                    checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)  # No margins
                    checkbox_layout.addWidget(checkbox_durum)
                    self.anapencere.tableWidgetMakineParametreSecim.setCellWidget(rowPosition, 8, checkbox_widget)

                i += 1
            else:
                pass
            self.anapencere.tableWidgetMakineParametreSecim.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.Stretch)
            self.anapencere.tableWidgetMakineParametreSecim.setSortingEnabled(True)
        except Exception as e:
            self.log_yaz("MAKINE PARAMETRE YENİLEME SAYFASI")

    def checkboxChanged(self, state, id):
        if state == QtCore.Qt.Checked:
            print(f"Checkbox checked for id: {id}")
        else:
            print(f"Checkbox unchecked for id: {id}")

    def makineParametreKaydet(self):
        try:
            makineAdi = self.anapencere.comboBoxParametreSecimMakineAdi.currentText()
            self.database_cursor.execute(f"Select Makine_Id from Makine_Tbl Where Makine_Ad='{makineAdi}' ")
            makineBilgi = self.database_cursor.fetchone()
            if makineBilgi:
                makineId = int(makineBilgi[0])
                for row in range(self.anapencere.tableWidgetMakineParametreSecim.rowCount()):
                    # CheckBox kontrolü
                    checkbox_durum = self.anapencere.tableWidgetMakineParametreSecim.cellWidget(row, 7).findChild(
                        QtWidgets.QCheckBox)
                    if checkbox_durum.isChecked():
                        # Parametre değerlerini al
                        parametreIdx = self.anapencere.tableWidgetMakineParametreSecim.item(row, 0).text()
                        offset_no = self.anapencere.tableWidgetMakineParametreSecim.cellWidget(row, 4).text()
                        plc_db = self.anapencere.tableWidgetMakineParametreSecim.cellWidget(row, 6).text()

                        # SQL sorgusunu oluştur
                        sql = """
                            INSERT INTO Makine_Parametre_Tbl
                            (Makine_Idx, Parametre_Idx, Offset_No, PLC_DB) 
                            VALUES 
                            (%s, %s, %s, %s)
                        """
                        values = (makineId, parametreIdx, offset_no, plc_db)

                        # SQL sorgusunu çalıştır
                        try:
                            self.database_cursor.execute(sql, values)
                        except Exception as e:
                            print(f"Error inserting row {row}: {e}")
                            continue

                    else:
                        pass

                # Değişiklikleri kaydet
                self.local_db.commit()
        except Exception as e:
            self.log_yaz("MAKİNE PARAMETRE KAYITLARDA PROBLEM OLUŞTU :", str(e))

    def firmaBilgisi(self):
        try:
            self.anapencere.comboBoxParametreFirmaAdi.clear()
            self.database_cursor.execute(f"SELECT Firma_Ad from Firma_Tbl")
            gelen_data = self.database_cursor.fetchall()
            for row in gelen_data:
                self.anapencere.comboBoxParametreFirmaAdi.addItem(row[0])
        except Exception as e:
            self.log_yaz("FİRMA BİLGİSİ HATADA : ", str(e))

    def makineBilgisi(self):
        try:
            firmaAdi = self.anapencere.comboBoxParametreFirmaAdi.currentText()
            self.database_cursor.execute(f"SELECT Firma_Id from Firma_Tbl Where Firma_Ad ='{firmaAdi}'")
            firma_Id = self.database_cursor.fetchone()
            if firma_Id:
                self.anapencere.comboBoxParametreMakineAdi.clear()
                firma_Id = firma_Id[0]
                self.database_cursor.execute(f"SELECT Makine_Ad from Makine_Tbl Where Firma_Idx = '{firma_Id}'")
                gelen_data = self.database_cursor.fetchall()
                for row in gelen_data:
                    self.anapencere.comboBoxParametreMakineAdi.addItem(row[0])
            else:
                pass
        except Exception as e:
            self.log_yaz("FİRMA BİLGİSİ HATADA : ", str(e))

    def parametreMakineOzellik(self):
        try:
            makineAd = self.anapencere.comboBoxParametreMakineAdi.currentText()
            self.database_cursor.execute(f"Select Makine_Id from Makine_Tbl Where Makine_Ad = '{makineAd}'")
            gelen_data = self.database_cursor.fetchone()
            if gelen_data:
                makine_idx = gelen_data[0]
                self.database_cursor.execute(f"Select * From Makine_Parametre_Tbl Where Makine_Idx = '{makine_idx}'")
                gelen_data = self.database_cursor.fetchall()
                i = 1
                self.anapencere.tableWidgeMakineParametreOzellik.setRowCount(0)
                self.anapencere.tableWidgeMakineParametreOzellik.setSortingEnabled(False)

                if len(gelen_data) > 0:
                    for data in gelen_data:
                        rowPosition = self.anapencere.tableWidgeMakineParametreOzellik.rowCount()
                        self.anapencere.tableWidgeMakineParametreOzellik.insertRow(rowPosition)

                        item = QtWidgets.QTableWidgetItem(str(i))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setVerticalHeaderItem(rowPosition, item)

                        item = QtWidgets.QTableWidgetItem()
                        item.setData(Qt.DisplayRole, (str(data[0])))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 0, item)

                        item = QtWidgets.QTableWidgetItem(str(data[1]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 1, item)

                        item = QtWidgets.QTableWidgetItem(str(data[2]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 2, item)

                        item = QtWidgets.QTableWidgetItem(str(data[3]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 3, item)

                        item = QtWidgets.QTableWidgetItem(str(data[4]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 4, item)

                        item = QtWidgets.QTableWidgetItem(str(data[5]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 5, item)

                        item = QtWidgets.QTableWidgetItem(str(data[6]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 6, item)

                        item = QtWidgets.QTableWidgetItem(str(data[7]))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgeMakineParametreOzellik.setItem(rowPosition, 7, item)

                        i += 1
                else:
                    pass
                self.anapencere.tableWidgeMakineParametreOzellik.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
                self.anapencere.tableWidgeMakineParametreOzellik.setSortingEnabled(True)
            else:
                pass

        except Exception as e:
            self.log_yaz("DATABASE TABLO GÖSTERME HATASI", str(e))

    def baglantiAyarlariniYukle(self):
        try:
            with sqlite3.connect("datalar/portsDatabase.db", isolation_level=None) as connector:

                connector.row_factory = sqlite3.Row
                sqlite_cursor = connector.cursor()

                sqlite_cursor.execute("SELECT * FROM portdatabase WHERE ref='{}';".format(1))

                temporary_data = sqlite_cursor.fetchone()
                self.PLC_IP = temporary_data["PLC_IP"]
                self.anapencere.lineEditAyarlarPlcIp.setText(str(self.PLC_IP))
                self.PLC_DB = temporary_data["PLC_DB"]
                self.anapencere.spinBoxAyarlarPlcPort.setValue(int(self.PLC_DB))

                self.DB_USERNAME = temporary_data["DB_USERNAME"]
                self.anapencere.lineEditDatabaseUsername.setText(str(self.DB_USERNAME))
                self.DB_PASSWORD = temporary_data["DB_PASSWORD"]
                self.anapencere.lineEditDatabasePassword.setText(str(self.DB_PASSWORD))
                self.DB_SERVER = temporary_data["DB_SERVER"]
                self.anapencere.lineEditDatabaseServer.setText(str(self.DB_SERVER))
                self.DB_VERITABANI = temporary_data["DB_VERITABANI"]
                self.anapencere.lineEditDatabaseVeritabaniAdi.setText(str(self.DB_VERITABANI))

        except Exception as e:
            self.log_yaz("LOKAL SERVER BAGLANTI AYARLARINI YUKLEME HATASI", str(e))
            return False, "LOKAL SERVER BAGLANTI AYARLARINI YUKLEME HATASI: {}".format(e)
            pass

    def loginMenuOpenClose(self):
        try:
            if self.sender().isChecked():

                self.anapencere.stackedWidgetSagAcilirMenu.setCurrentWidget(self.anapencere.pageGirisCikisYap)
                self.anapencere.widgetSagAcilirMenu.setVisible(True)
                self.anapencere.widgetSagAcilirMenu.setMaximumSize(QtCore.QSize(250, 16777215))

                self.palet_detay_goster_sender = None
                self.sender().setStyleSheet(style_vars.buttons_menu_active)
            else:
                self.anapencere.widgetSagAcilirMenu.setVisible(False)
                self.sender().setStyleSheet(style_vars.buttons_menu_normal)
        except Exception as e:
            self.log_yaz("loginMenuOpenClose", "")
            pass

    def girisYapButon(self):
        try:
            kullanici_adi = self.anapencere.lineEditKullanici.text()
            kullanici_sifre = self.anapencere.lineEditSifre.text()

            if kullanici_adi == 'stu' and kullanici_sifre == 'optimak123':
                self.anapencere.pageAyarlar.setEnabled(True)
            else:
                self.anapencere.pageAyarlar.setEnabled(False)
        except Exception as e:
            self.log_yaz("Giriş Yaparken Hata Oluştu : ", str(e))

    def cikisYapButon(self):
        try:
            self.anapencere.pageAyarlar.setEnabled(False)
        except Exception as e:
            self.log_yaz("SISTEM CIKIS HATASI : ", e)

    def widgetSagAcilirMenuKapatButon(self):
        try:
            self.anapencere.widgetSagAcilirMenu.setVisible(False)
            self.palet_detay_goster_sender = None
            self.anapencere.pushButtonOpenLoginMenu.setChecked(False)
            self.anapencere.pushButtonOpenLoginMenu.setStyleSheet(style_vars.buttons_menu_normal)
        except:
            pass

    def buton_menu_toggle(self):
        if self.sender().text() == "":
            buton_liste = self.sender().parentWidget().findChildren(QtWidgets.QPushButton)
            for butonn in buton_liste:
                butonn.setText(butonn.toolTip().ljust(15, " "))
                butonn.setMinimumSize(QtCore.QSize(145, 0))
            self.sender().parentWidget().setMinimumSize(QtCore.QSize(150, 0))

        elif self.sender().text() == self.sender().toolTip().ljust(15, " "):
            buton_liste = self.sender().parentWidget().findChildren(QtWidgets.QPushButton)
            for butonn in buton_liste:
                butonn.setMinimumSize(QtCore.QSize(40, 0))
                butonn.setText("")

            self.sender().parentWidget().setMinimumSize(QtCore.QSize(45, 0))

    def switchToOtherMainPage(self):
        # signal slot baglantısı Designer Uzerinden yapılmıstır
        pageName = self.sender().objectName().replace("pushButtonSwitchTo", "")
        self.clear_menu_button_styls(self.sender())

        switchPage = self.findChild(QtWidgets.QWidget, pageName)
        switchPage.parentWidget().setCurrentWidget(switchPage)
        self.sender().setStyleSheet(style_vars.buttons_menu_active)

        primaryPage = self.anapencere.stackedWidgetMenuler.currentWidget().objectName()

        if primaryPage == "pageLog":
            QtCore.QTimer.singleShot(100, lambda: self.loadLogDatabase())
            self.yeni_log_durumu = False

        elif primaryPage == "pageDatabase":
            self.basilanEtiketlerTablosuYenile()

        elif primaryPage == "pageMakineParametreSecim":
            self.makineParametreSecimYenile()

        elif primaryPage == "pageMakineParametre":
            self.firmaBilgisi()

        elif primaryPage == "pageMakine":
            secondaryPage = self.anapencere.stackedWidgetMakine.currentWidget().objectName()
            if secondaryPage == "pageMakineEkle":
                self.anapencere.lineEditMakineAdi.setEnabled(True)
                self.anapencere.lineEditMakinePlcIp.setEnabled(True)
            elif secondaryPage == "pageMakineListele":
                self.MakineYenile()

        elif primaryPage == "pageFirma":
            secondaryPage = self.anapencere.stackedWidgetFirma.currentWidget().objectName()
            if secondaryPage == "pageFirmaEkle":
                self.anapencere.lineEditFirmaAdi.setEnabled(True)
                self.anapencere.lineEditAciklama.setEnabled(True)
                self.anapencere.lineEditPcIp.setEnabled(True)
                self.anapencere.lineEditSecomeaNickname.setEnabled(True)
                self.anapencere.lineEditSecomeaKopru.setEnabled(True)
            elif secondaryPage == "pageFirmaListele":
                self.FirmaYenile()

        elif primaryPage == "pageParametre":
            secondaryPage = self.anapencere.stackedWidgetParametre.currentWidget().objectName()
            if secondaryPage == "pageParametreEkle":
                pass
            elif secondaryPage == "pageParametreGoruntuleme":
                self.ParametreYenile()

    def clear_menu_button_styls(self, sender):
        try:
            buton_liste = sender.parentWidget().findChildren(QtWidgets.QPushButton)
            for butonn in buton_liste:
                if butonn.objectName() == "pushButtonSwitchTopageLog":
                    if not self.yeni_log_durumu:
                        butonn.setStyleSheet(style_vars.buttons_menu_normal)
                elif butonn.objectName() == "pushButtonOpenLoginMenu":
                    continue
                elif butonn.objectName() == "pushButtonClose":
                    continue
                else:
                    butonn.setStyleSheet(style_vars.buttons_menu_normal)

        except Exception as e:
            print("clear menu button styls exception", e)
            pass

    def statusShow(self):
        # if len(self.plc_istek_list) > 0:
            # self.anapencere.listWidgetPlcIstekList_1.clear()
            # for istek in self.plc_istek_list:
            #     item = QtWidgets.QListWidgetItem()
            #     item.setText(istek)
            #     self.anapencere.listWidgetPlcIstekList_1.addItem(item)
            # son_satir = self.anapencere.listWidgetPlcIstekList_1.count()
            # son_item = self.anapencere.listWidgetPlcIstekList_1.item(son_satir - 1)
            # son_item.setBackground(QtGui.QColor('#7fc97f'))

        self.statusVariable += 5
        if self.statusVariable > 100:
            self.statusVariable = 0

        value = self.statusVariable

        progress = (100 - value) / 100.0

        stop_array = [None, None, None, None, None, None, None, None]

        stop_array[0] = progress
        stop_array[1] = progress + 0.002
        stop_array[2] = progress + 0.262
        stop_array[3] = progress + 0.264
        stop_array[4] = progress + 0.502
        stop_array[5] = progress + 0.504
        stop_array[6] = progress + 0.762
        stop_array[7] = progress + 0.764

        for i in range(0, 8):
            if stop_array[i] > 1:
                stop_array[i] = stop_array[i] - 1

        for i in range(0, 8):
            stop_array[i] = str(stop_array[i])
        mini_gosterge_styleSheet = style_vars.status_gosterge_styleSheet \
            .replace("{STOP_1_1}", stop_array[0]) \
            .replace("{STOP_1_2}", stop_array[1]) \
            .replace("{STOP_2_1}", stop_array[2]) \
            .replace("{STOP_2_2}", stop_array[3]) \
            .replace("{STOP_3_1}", stop_array[4]) \
            .replace("{STOP_3_2}", stop_array[5]) \
            .replace("{STOP_4_1}", stop_array[6]) \
            .replace("{STOP_4_2}", stop_array[7])

        self.anapencere.statusGostergeProgress.setStyleSheet(mini_gosterge_styleSheet)

    def loadLogDatabase(self):
        # todo: başka yere taşınacak
        try:
            with sqlite3.connect("datalar/logDatabase.db", isolation_level=None) as connector:
                self.isLogFilterVisible()
                connector.row_factory = sqlite3.Row
                sqlite_cursor = connector.cursor()
                sqlite_cursor.execute("SELECT * FROM log_kayitlari")

                tarih_filtre = self.anapencere.lineEditLogFiltreTarih.text()
                kaynak_filtre = self.anapencere.lineEditLogFiltreKaynak.text()
                log_yazisi_filtre = self.anapencere.lineEditLogFiltreHata.text()

                sqlite_cursor.execute(
                    """SELECT tarih, kaynak, log_yazisi FROM log_kayitlari WHERE tarih LIKE "%{tarih_filtre}%" AND 
                    kaynak LIKE "%{kaynak_filtre}%" AND log_yazisi LIKE "%{log_yazisi_filtre}%" ORDER BY 
                    ref;""".replace(
                        "{tarih_filtre}", tarih_filtre).
                        replace("{kaynak_filtre}", kaynak_filtre).replace("{log_yazisi_filtre}", log_yazisi_filtre))

                gelen_data = sqlite_cursor.fetchall()
                if len(gelen_data) != 0:
                    self.anapencere.widgetLogKaydiYokUyarisi.setVisible(False)
                    self.anapencere.tableWidgetLog.setVisible(True)
                    self.anapencere.tableWidgetLog.setSortingEnabled(False)
                    self.anapencere.tableWidgetLog.setRowCount(0)
                    for data in gelen_data:
                        rowPosition = self.anapencere.tableWidgetLog.rowCount()
                        self.anapencere.tableWidgetLog.insertRow(rowPosition)

                        item = QtWidgets.QTableWidgetItem(str(rowPosition + 1))
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                        self.anapencere.tableWidgetLog.setVerticalHeaderItem(rowPosition, item)

                        item = QtWidgets.QTableWidgetItem()
                        log_tarih = QDateTime.fromString(data["tarih"], "dd-MM-yyyy hh:mm:ss")
                        item.setData(Qt.DisplayRole, log_tarih)

                        self.anapencere.tableWidgetLog.setItem(rowPosition, 0, item)
                        self.anapencere.tableWidgetLog.setItem(rowPosition, 1,
                                                               QtWidgets.QTableWidgetItem(str(data["kaynak"])))
                        self.anapencere.tableWidgetLog.setItem(rowPosition, 2,
                                                               QtWidgets.QTableWidgetItem(str(data["log_yazisi"])))

                    self.anapencere.tableWidgetLog.resizeColumnsToContents()
                    self.anapencere.tableWidgetLog.setSortingEnabled(True)
                    self.anapencere.tableWidgetLog.sortByColumn(0, Qt.DescendingOrder)

                    maxwidth = self.anapencere.tableWidgetLog.verticalHeader().sectionSize(0)
                    self.anapencere.pushButtonLogFiltreEnable.setMinimumWidth(maxwidth)
                    self.anapencere.pushButtonLogFiltreEnable.setMaximumSize(maxwidth, 35)

                    maxwidth = self.anapencere.tableWidgetLog.horizontalHeader().sectionSize(0)
                    self.anapencere.lineEditLogFiltreTarih.setMinimumWidth(maxwidth)
                    self.anapencere.lineEditLogFiltreTarih.setMaximumSize(maxwidth, 30)

                    maxwidth = self.anapencere.tableWidgetLog.horizontalHeader().sectionSize(1)
                    self.anapencere.lineEditLogFiltreKaynak.setMinimumWidth(maxwidth)
                    self.anapencere.lineEditLogFiltreKaynak.setMaximumSize(maxwidth, 30)
                    # self.anapencere.widgetLogFiltreleri.layout().setContentsMargins(0, 0, 0, 0)
                else:
                    self.anapencere.tableWidgetLog.setVisible(False)
                    self.anapencere.widgetLogKaydiYokUyarisi.setVisible(True)
        except Exception as e:
            print(e)
            pass

    def isLogFilterVisible(self):
        self.anapencere.widgetLogFiltreleri.setVisible(self.anapencere.pushButtonLogFiltreEnable.isChecked())

    def log_yaz(self, kaynak, log_yazisi):
        try:
            self.yeni_log_durumu = True
            #self.anapencere.labelSayfaAltiLog.setText("{}: {}".format(kaynak, log_yazisi))
            self.anapencere.pushButtonSwitchTopageLog.setStyleSheet(style_vars.red_background)
            python_date = QDateTime.currentDateTime().toPyDateTime()
            datestring = python_date.strftime("%d-%m-%Y %H:%M:%S")
            log_yazisi = log_yazisi.replace('"', "'")

            with sqlite3.connect("datalar/logDatabase.db", isolation_level=None) as connector:
                connector.row_factory = sqlite3.Row
                sqlite_cursor = connector.cursor()
                sqlite_cursor.execute(
                    "CREATE TABLE IF NOT EXISTS log_kayitlari (ref INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT,"
                    "tarih	TEXT,"
                    "kaynak TEXT,"
                    "log_yazisi	TEXT);")

                sqlite_cursor.execute(
                    "DELETE FROM {} where ref NOT IN( select ref from (select ref from {} order by ref desc LIMIT "
                    "{}) x); "
                    "".format("log_kayitlari", "log_kayitlari", 10000))

                command = """INSERT INTO log_kayitlari (tarih, kaynak, log_yazisi) VALUES ("{tarih}", "{kaynak}", 
                "{log_yazisi}");""".replace("{tarih}", datestring).replace("{kaynak}", str(kaynak)).replace(
                    "{log_yazisi}", log_yazisi)
                sqlite_cursor.execute(command)
        except Exception as e:
            print("log exception: ", e)
            pass

    def closeEvent(self, event):
        try:
            password_dialog = MyPasswordDialog()
            if password_dialog.exec_() == QDialog.Accepted:
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            print("e", str(e))
            pass

class MyPasswordDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Şifre Etiketi ve Düzeni
        self.label = QLabel("PLEASE ENTER PASSWORD :")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_button = QPushButton("OK")
        self.password_button.clicked.connect(self.check_password)

        self.setStyleSheet("QWidget { background-color: #222; color: #fff; }")
        self.setWindowTitle("EXIT")

        # Düzenleme
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.password_button)
        self.setLayout(layout)

    def check_password(self):
        if self.password_edit.text() == "12345":
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Yanlış Şifre")

class SplashScreen(QtWidgets.QMainWindow, Ui_SplashScreen):
    def __init__(self, parent=None):

        super(SplashScreen, self).__init__(parent=parent)

        self.splashpencere = Ui_SplashScreen()
        self.splashpencere.setupUi(self)

        self.splashpencere.pushButtonCancel.clicked.connect(self.buton_cancel)

        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.splashpencere.progressBar.setValue(0)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(255, 255, 255, 250))
        self.splashpencere.centralwidget.setGraphicsEffect(self.shadow)
        self.splashpencere.labelSoftwareVersion.setText("Version: 1.0 @2024")

        self.prograss_thread = SplashScreenThreadClass()
        self.prograss_thread.thread_kontrol_sinyal.connect(self.progress)
        self.thread_baslat()

    def buton_cancel(self):
        self.thread_durdur()
        self.close()

    def thread_baslat(self):
        self.prograss_thread.start()

    def thread_durdur(self):
        self.prograss_thread.terminate()

    def progress(self, ilerleme, durum):

        if ilerleme == 1:
            self.splashpencere.label_description.setText("SYSTEM CONNECTION CONTROL")
        if ilerleme == 20:
            self.splashpencere.progressBar.setValue(ilerleme)
            if durum:
                self.splashpencere.listWidgetIslemler.addItem("PLC 1 BAGLANDI")
            else:
                self.splashpencere.listWidgetIslemler.addItem("!!! PLC 1 BAGLANAMADI")
        if ilerleme == 21:
            self.splashpencere.label_description.setText("IFS CONNECTION CONTROL")
        if ilerleme == 40:
            self.splashpencere.progressBar.setValue(ilerleme)
            if durum:
                self.splashpencere.listWidgetIslemler.addItem("IFS BAGLANDI")
            else:
                self.splashpencere.listWidgetIslemler.addItem("!!! IFS BAGLANAMADI")


        if ilerleme == 61:
            self.splashpencere.label_description.setText("DATABASE CONNECTING")
        if ilerleme == 80:
            self.splashpencere.progressBar.setValue(ilerleme)
            if durum == 0:
                self.splashpencere.listWidgetIslemler.addItem("DATABASE BAGLANDI")
            else:
                self.splashpencere.listWidgetIslemler.addItem("!!! DATABASE CANNOT BAGLANDI")

        if ilerleme == 100:
            self.splashpencere.progressBar.setValue(ilerleme)
            self.splashpencere.label_description.setText("<strong> CONNECTION CONTROLS FINISHED</strong>")

        if ilerleme == 101:
            self.prograss_thread.anapencere_show()
            self.thread_durdur()
            self.close()

class SplashScreenThreadClass(QtCore.QThread):
    thread_kontrol_sinyal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(SplashScreenThreadClass, self).__init__(parent)
        self.anapencere = MainWindow()

    def run(self):
        try:
            sure = 1
            self.thread_kontrol_sinyal.emit(10, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(20, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(30, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(40, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(50, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(60, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(70, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(80, True)
            time.sleep(sure)
            self.thread_kontrol_sinyal.emit(101, True)

            """
            self.thread_kontrol_sinyal.emit(1, False)
            if self.anapencere.plc_connect():
                self.thread_kontrol_sinyal.emit(20, True)
            else:
                self.thread_kontrol_sinyal.emit(20, False)

            self.thread_kontrol_sinyal.emit(21, False)
            if self.anapencere.rest_api_connect():
                self.thread_kontrol_sinyal.emit(40, True)
            else:
                self.thread_kontrol_sinyal.emit(40, False)

            self.thread_kontrol_sinyal.emit(41, False)
            if self.anapencere.barcode_reader_connect():
                self.thread_kontrol_sinyal.emit(60, True)
            else:
                self.thread_kontrol_sinyal.emit(60, False)

            self.thread_kontrol_sinyal.emit(61, False)

            status = self.anapencere.printer_connect()
            self.thread_kontrol_sinyal.emit(80, status)

            self.thread_kontrol_sinyal.emit(100, False)
            time.sleep(1)
            self.thread_kontrol_sinyal.emit(101, False)
            """
        except:
            pass
        pass

    def anapencere_show(self):
        self.anapencere.show()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("datalar/optimak.ico"))
    pencere = SplashScreen()
    pencere.show()
    sys.exit(app.exec_())
