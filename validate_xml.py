from lxml import etree

XML_FILE = "Converti.xml"
XSD_FILE = "modele.xsd"

def validate_xml(xml_file, xsd_file):
    # Charger le schéma XSD
    with open(xsd_file, 'rb') as f:
        schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)

    # Charger le fichier XML
    with open(xml_file, 'rb') as f:
        xml_doc = etree.parse(f)

    # Validation
    is_valid = schema.validate(xml_doc)
    if is_valid:
        print("Le fichier XML est valide selon le XSD.")
    else:
        print("Le fichier XML n'est PAS valide !")
        for error in schema.error_log:
            print(f"Ligne {error.line}: {error.message}")

if __name__ == "__main__":
    validate_xml(XML_FILE, XSD_FILE)