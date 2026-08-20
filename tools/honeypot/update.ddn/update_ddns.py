import sys  
import requests  
import subprocess  
import json  
from PyQt5 import QtWidgets

def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)

def update_dns(config):
    try:
        new_ip = requests.get("http://api.ipify.org").text  
        command = f"Add-DnsServerResourceRecordA -Name {config['record_name']} -ZoneName {config['zone_name']} -IPv4Address {new_ip} -ComputerName {config['dns_server']} -CreatePtr"
        subprocess.run(["powershell", "-Command", command], check=True)
        QtWidgets.QMessageBox.information(None, "Succès", f"Mise à jour réussie : {config['record_name']} pointe maintenant vers {new_ip}")
    except requests.RequestException as e:
        QtWidgets.QMessageBox.critical(None, "Erreur", f"Erreur lors de la récupération de l'IP publique : {e}")
    except subprocess.CalledProcessError as e:
        QtWidgets.QMessageBox.critical(None, "Erreur", f"Erreur lors de la mise à jour de l'enregistrement DNS : {e}")

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Mise à jour DDNS")
        self.setGeometry(100, 100, 300, 200)

        button = QtWidgets.QPushButton("Mettre à jour DDNS", self)
        button.clicked.connect(self.run_update)
        button.setGeometry(50, 80, 200, 40)

    def run_update(self):
        config = load_config()
        update_dns(config)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()