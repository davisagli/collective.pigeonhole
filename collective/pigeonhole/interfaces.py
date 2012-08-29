from zope import schema
from zope.interface import Interface
from plone.schemaeditor.interfaces import ISchemaContext


class IPigeonholeSchemaSettings(Interface):

    title = schema.TextLine(title=u'Title')
    name = schema.ASCIILine(title=u'Name')
    schema_xml = schema.Text(title = u'Schema XML')
    types = schema.Set(
        value_type = schema.Choice(
            vocabulary = 'plone.app.vocabulary.ReallyUserFriendlyTypes',
            )
        )
    condition = schema.ASCIILine(
        title = u'Condition',
        description=u'A TALES expression. If specified, it must evaluate to true in order to show the schema.',
        required = False)


class IPigeonholeSchema(ISchemaContext):
    pass
