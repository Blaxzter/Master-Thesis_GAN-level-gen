from xml.dom.minidom import Document

from level.Level import Level


def create_camera(doc):
    camera = doc.createElement('Camera')
    camera.setAttribute('x', str(0))
    camera.setAttribute('y', str(2))
    camera.setAttribute('minWidth', str(20))
    camera.setAttribute('maxWidth', str(30))
    return camera


def create_birds(doc, level: Level):
    birds = doc.createElement('Birds')
    for level_bird in level.birds:
        xml_bird = doc.createElement('Bird')
        xml_bird.setAttribute('type', str(level_bird.type))
        birds.appendChild(xml_bird)
    return birds


def create_slingshot(doc):
    slingshot = doc.createElement('Slingshot')
    slingshot.setAttribute('x', str(-8))
    slingshot.setAttribute('y', str(-2.5))
    return slingshot


def create_basis_level_node(level: Level):
    doc = Document()
    doc.encoding = 'utf-8'
    node = doc.createElement('Level')
    node.setAttribute('width', str(2))
    node.appendChild(create_camera(doc))
    node.appendChild(create_birds(doc, level))
    node.appendChild(create_slingshot(doc))

    return doc, node
