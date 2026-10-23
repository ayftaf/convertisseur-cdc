import csv
import sys
from lxml import etree
from datetime import datetime
import uuid

# --- CONFIGURATION ---
CSV_FILE = ".csv"
XML_FILE = "Converti.xml"
NAMESPACE = "urn:cdc:cpf:pc5:schema:1.0.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
NSMAP = {"cpf": NAMESPACE, "xsi": XSI_NAMESPACE}

# --- HELPERS ---

def safe_bool(val):
    if isinstance(val, bool):
        return val
    if val is None:
        return "false"
    return "true" if str(val).strip().lower() in ("true", "1", "vrai", "oui", "x") else "false"

def format_date(date_str):
    # Accepts DD/MM/YYYY or YYYY-MM-DD, returns YYYY-MM-DD
    if not date_str or not date_str.strip():
        return None
    try:
        if "/" in date_str:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return None

def format_datetime_now():
    # Returns current datetime in XSD pattern: 2025-06-27T14:00:00+01:00
    now = datetime.now()
    offset = "+01:00"
    return now.strftime("%Y-%m-%dT%H:%M:%S") + offset

def add_elem(parent, tag, value, nillable=False, min_length=None):
    # Ne pas créer la balise si optionnelle et vide
    if (value is None or value == "") and not nillable:
        return None
    if min_length and value is not None and len(str(value)) < min_length:
        return None
    elem = etree.SubElement(parent, f"{{{NAMESPACE}}}{tag}")
    if nillable and (value is None or value == ""):
        elem.set(f"{{{XSI_NAMESPACE}}}nil", "true")
    elif value is not None:
        elem.text = str(value)
    return elem

# --- MAIN ---

def main():
    # Read CSV
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    # Group by certificateur/certification
    flux_id = "FLUX2021"
    horodatage = format_datetime_now()
    emetteur_idClient = "00000000"  # TODO: set your idClient emetteur

    # Build XML
    flux = etree.Element(f"{{{NAMESPACE}}}flux", nsmap=NSMAP)
    add_elem(flux, "idFlux", flux_id)
    add_elem(flux, "horodatage", horodatage)

    emetteur = etree.SubElement(flux, f"{{{NAMESPACE}}}emetteur")
    add_elem(emetteur, "idClient", emetteur_idClient)
    certificateurs = etree.SubElement(emetteur, f"{{{NAMESPACE}}}certificateurs")

    # Group rows by certificateur_idClient/idContrat/type/code
    certif_groups = {}
    for row in rows:
        try:
            key = (
                row["idClientCertificateur"].strip(),
                row["idContrat"].strip(),
                row["typeCertification"].strip(),
                row["codeCertification"].strip()
            )
        except KeyError as e:
            print("Colonne manquante :", e)
            print("Colonnes disponibles :", row.keys())
            sys.exit(1)
        certif_groups.setdefault(key, []).append(row)

    for (idClient, idContrat, typeCert, codeCert), group_rows in certif_groups.items():
        certificateur = etree.SubElement(certificateurs, f"{{{NAMESPACE}}}certificateur")
        add_elem(certificateur, "idClient", idClient.zfill(8))
        add_elem(certificateur, "idContrat", idContrat)
        certifications = etree.SubElement(certificateur, f"{{{NAMESPACE}}}certifications")
        certification = etree.SubElement(certifications, f"{{{NAMESPACE}}}certification")
        add_elem(certification, "type", typeCert)
        add_elem(certification, "code", codeCert)
        # Optionnel : natureDeposant
        if row.get("natureDeposant"):
            add_elem(certification, "natureDeposant", row["natureDeposant"])
        passageCertifications = etree.SubElement(certification, f"{{{NAMESPACE}}}passageCertifications")

        for row in group_rows:
            # Vérifie si la ligne contient au moins une info obligatoire pour passageCertification
            champs_obligatoires = [
                row.get("obtentionCertification", ""),
                row.get("donneeCertifiee", ""),
                row.get("dateDebutValidite", ""),
                row.get("presenceNiveauLangueEuro", ""),
                row.get("presenceNiveauNumeriqueEuro", ""),
                row.get("nomNaissance", ""),
                row.get("prenom1", ""),
                row.get("anneeNaissance", ""),
                row.get("sexe", "")
            ]
            if not any(str(champ).strip() for champ in champs_obligatoires):
                continue  # Ignore la ligne si tout est vide

            passageCertification = etree.SubElement(passageCertifications, f"{{{NAMESPACE}}}passageCertification")
            id_technique = str(uuid.uuid4())
            add_elem(passageCertification, "idTechnique", id_technique)
            add_elem(passageCertification, "urlPreuve", row.get("urlPreuve",""), nillable=False)
            add_elem(passageCertification, "libelleOption", row.get("libelleOption",""), nillable=False)
            add_elem(passageCertification, "obtentionCertification", row.get("obtentionCertification", "PAR_ADMISSION"))
            add_elem(passageCertification, "donneeCertifiee", safe_bool(row.get("donneeCertifiee", "false")))
            add_elem(passageCertification, "dateDebutExamen", format_date(row.get("dateDebutExamen")), nillable=False)
            add_elem(passageCertification, "dateFinExamen", format_date(row.get("dateFinExamen")), nillable=False)
            add_elem(passageCertification, "modalitePassageExamen", row.get("modalitePassageExamen", "").strip(), nillable=False)
            add_elem(passageCertification, "codePostalCentreExamen", row.get("codePostalCentreExamen",""), nillable=False)
            add_elem(passageCertification, "dateDebutValidite", format_date(row.get("dateDebutValidite")))
            # dateFinValidite (nillable)
            dfv = format_date(row.get("dateFinValidite"))
            add_elem(passageCertification, "dateFinValidite", dfv, nillable=True)
            add_elem(passageCertification, "presenceNiveauLangueEuro", safe_bool(row.get("presenceNiveauLangueEuro", "false")))
            add_elem(passageCertification, "niveauLangueEuropeen", row.get("niveauLangueEuropeen",""), nillable=False)
            add_elem(passageCertification, "presenceNiveauNumeriqueEuro", safe_bool(row.get("presenceNiveauNumeriqueEuro", "false")))
            add_elem(passageCertification, "niveauNumeriqueEuropeen", row.get("niveauNumeriqueEuropeen",""), nillable=False)
            add_elem(passageCertification, "scoring", row.get("scoring",""), nillable=True)
            add_elem(passageCertification, "mentionValidee", row.get("mentionValidee",""), nillable=True)

            # modalitesInscription
            modalitesInscription = etree.SubElement(passageCertification, f"{{{NAMESPACE}}}modalitesInscription")
            add_elem(modalitesInscription, "modaliteAcces", row.get("modaliteAcces",""), nillable=True)
            add_elem(modalitesInscription, "voieAccessVAE", row.get("voieAccessVAE",""), nillable=False)
            add_elem(modalitesInscription, "initiativeInscription", row.get("initiativeInscription",""), nillable=False)
            add_elem(modalitesInscription, "dateInscription", format_date(row.get("dateInscription")), nillable=False)

            # identificationTitulaire (toujours titulaire dans ce CSV)
            identificationTitulaire = etree.SubElement(passageCertification, f"{{{NAMESPACE}}}identificationTitulaire")
            titulaire = etree.SubElement(identificationTitulaire, f"{{{NAMESPACE}}}titulaire")
            add_elem(titulaire, "nomNaissance", row.get("nomNaissance",""))
            add_elem(titulaire, "nomUsage", row.get("nomUsage",""), nillable=True)
            add_elem(titulaire, "prenom1", row.get("prenom1",""))
            add_elem(titulaire, "prenom2", row.get("prenom2",""), min_length=1)
            add_elem(titulaire, "prenom3", row.get("prenom3",""), min_length=1)
            annee = row.get("anneeNaissance","")
            add_elem(titulaire, "anneeNaissance", annee if annee else "1900")
            add_elem(titulaire, "moisNaissance", row.get("moisNaissance",""), nillable=True)
            add_elem(titulaire, "jourNaissance", row.get("jourNaissance",""), nillable=True)
            add_elem(titulaire, "sexe", row.get("sexe","M"))
            # codeCommuneNaissance
            codeCommuneNaissance = etree.SubElement(titulaire, f"{{{NAMESPACE}}}codeCommuneNaissance")
            codeInsee = row.get("codeInseeNaissance","")
            if codeInsee:
                codeInseeNaissance = etree.SubElement(codeCommuneNaissance, f"{{{NAMESPACE}}}codeInseeNaissance")
                add_elem(codeInseeNaissance, "codeInsee", codeInsee)
            else:
                codePostal = row.get("codePostalNaissance","")
                codePostalNaissance = etree.SubElement(codeCommuneNaissance, f"{{{NAMESPACE}}}codePostalNaissance")
                add_elem(codePostalNaissance, "codePostal", codePostal, nillable=True)
            add_elem(titulaire, "libelleCommuneNaissance", row.get("libelleCommuneNaissance",""), nillable=False)
            add_elem(titulaire, "codePaysNaissance", row.get("codePaysNaissance",""), nillable=False)
            add_elem(titulaire, "libellePaysNaissance", row.get("libellePaysNaissance",""), nillable=False)
            add_elem(titulaire, "commentairesMEN", row.get("commentairesMEN",""), nillable=False)
            add_elem(passageCertification, "verbatim", row.get("verbatim",""), min_length=1)

    # Write XML
    tree = etree.ElementTree(flux)
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    main()