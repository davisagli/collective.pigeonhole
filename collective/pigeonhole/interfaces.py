from zope import schema
from zope.interface import Interface, Invalid
from plone.schemaeditor.interfaces import ISchemaContext

from Products.PageTemplates.Expressions import getEngine


def isValidExpression(value):
    try:
        getEngine().compile(value)
    except:
        raise Invalid(u'Please enter a valid TALES expression.')
    return True


class IPigeonholeSchemaSettings(Interface):

    title = schema.TextLine(title=u'Title')
    name = schema.ASCIILine(title=u'Name')
    schema_xml = schema.ASCII(title = u'Schema XML', default='<model xmlns="http://namespaces.plone.org/supermodel/schema"><schema></schema></model>')
    types = schema.Set(
        value_type = schema.Choice(
            vocabulary = 'plone.app.vocabularies.ReallyUserFriendlyTypes',
            )
        )
    condition = schema.ASCIILine(
        title = u'Condition',
        description=u'A TALES expression. If specified, it must evaluate to true in order to show the schema.',
        required = False,
        constraint = isValidExpression,
        )


class IPigeonholeSchema(ISchemaContext):
    pass
