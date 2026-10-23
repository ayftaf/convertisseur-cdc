from lxml import etree

xsd_file = 'modele.xsd'
xml_file = '2021.xml'

with open(xsd_file) as xsd, open(xml_file) as xml:
    schema_doc = etree.parse(xsd)
    schema = etree.XMLSchema(schema_doc)
    xml_doc = etree.parse(xml)
    if schema.validate(xml_doc):
        print("XML valide.")
    else:
        print("XML invalide.")
        for error in schema.error_log:
            print(error.message)

