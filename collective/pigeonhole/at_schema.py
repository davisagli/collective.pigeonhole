from zope.interface import implements
from zope.component import adapts, getUtility
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import ISet, IList, IChoice
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.field import ExtensionField
from plone.registry.interfaces import IRegistry
import plone.supermodel

from Products.Archetypes import atapi
from Products.Archetypes.interfaces import IBaseObject

from collective.pigeonhole.interfaces import IPigeonholeSchemaSettings
from collective.pigeonhole.interfaces import IPigeonholeSchema
from collective.pigeonhole import REGISTRY_BASE_PREFIX


class StringField(ExtensionField, atapi.StringField):
    pass

class LinesField(ExtensionField, atapi.LinesField):
    pass


class PigeonholeSchemaExtender(object):
    implements(ISchemaExtender)
    adapts(IBaseObject)
       
    def __init__(self, context):
        self.context = context
    
    def getFields(self):
        registry = getUtility(IRegistry)
        schemas = registry.collectionOfInterface(IPigeonholeSchemaSettings, prefix=REGISTRY_BASE_PREFIX)

        fields = []
        for schema_name, settings in schemas.items():
            # XXX type and condition filters

            # XXX cache
            schema = plone.supermodel.loadString(settings.schema_xml).schema

            for field_name, field in getFieldsInOrder(schema):
                if IChoice.providedBy(field):
                    fields.append(StringField(
                        schema_name + '.' + field.__name__,
                        required=field.required,
                        schemata='categorization',
                        widget=atapi.SelectionWidget(
                            label = field.title,
                            description = field.description,
                            ),
                        vocabulary = atapi.DisplayList([(t.value, t.title or t.token) for t in field.vocabulary]),
                        ))
                elif IList.providedBy(field) and IChoice.providedBy(field.value_type): # XXX should be set
                    fields.append(LinesField(
                        schema_name + '.' + field.__name__,
                        required=field.required,
                        schemata='categorization',
                        widget=atapi.MultiSelectionWidget(
                            label = field.title,
                            description = field.description,
                            ),
                        vocabulary = atapi.DisplayList([(t.value, t.title or t.token) for t in field.value_type.vocabulary]),
                        ))
        return fields
