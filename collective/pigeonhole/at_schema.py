from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.component import adapts, getUtility
from zope.globalrequest import getRequest
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import ISet, IChoice
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.field import ExtensionField
from plone.memoize import volatile
from plone.registry.interfaces import IRegistry
import plone.supermodel

from Products.CMFCore.Expression import Expression, getExprContext
from Products.Archetypes import atapi
from Products.Archetypes.interfaces import IBaseObject

from collective.pigeonhole.interfaces import IPigeonholeSchemaSettings
from collective.pigeonhole import REGISTRY_BASE_PREFIX


class StringField(ExtensionField, atapi.StringField):
    pass

class LinesField(ExtensionField, atapi.LinesField):
    pass


def _cache_key(self, *args, **kw):
    return

def _request_cache(func, *args, **kw):
    request = getRequest()
    if request is not None:
        return IAnnotations(request)
    return {}


class PigeonholeSchemaExtender(object):
    implements(ISchemaExtender)
    adapts(IBaseObject)
       
    def __init__(self, context):
        self.context = context
    
    @volatile.cache(_cache_key, get_cache=_request_cache)
    def _getSchemaInfo(self):
        registry = getUtility(IRegistry)
        schema_info = registry.collectionOfInterface(IPigeonholeSchemaSettings, prefix=REGISTRY_BASE_PREFIX)
        res = []
        for schema_name, settings in schema_info.items():
            schema = plone.supermodel.loadString(settings.schema_xml).schema
            if settings.condition:
                condition = Expression(settings.condition)
            else:
                condition = None
            res.append((schema_name, settings, condition, schema))
        return res

    @volatile.cache(_cache_key, get_cache=volatile.store_on_context)
    def _getSchemas(self):
        schemas = []
        for schema_name, settings, condition, schema in self._getSchemaInfo():
            types = settings.types
            if 'File' in types:
                types = types | set(['Blob'])
            if self.context.portal_type not in types:
                continue

            if condition is not None and getattr(self.context, 'REQUEST', None) is getRequest():
                econtext = getExprContext(self.context, self.context)
                if not Expression(settings.condition)(econtext):
                    continue

            schemas.append((schema_name, schema))

        return schemas

    def getFields(self):
        fields = []
        for schema_name, schema in self._getSchemas():
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
                elif ISet.providedBy(field) and IChoice.providedBy(field.value_type): # XXX should be set
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
