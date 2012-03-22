# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'RainappConfig.slug'
        db.add_column('lizard_rainapp_rainappconfig', 'slug', self.gf('django.db.models.fields.SlugField')(default='', max_length=50, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'RainappConfig.slug'
        db.delete_column('lizard_rainapp_rainappconfig', 'slug')


    models = {
        'lizard_fewsjdbc.jdbcsource': {
            'Meta': {'object_name': 'JdbcSource'},
            'connector_string': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'customfilter': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filter_tree_root': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jdbc_tag_name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'jdbc_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'usecustomfilter': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'lizard_map.setting': {
            'Meta': {'object_name': 'Setting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'lizard_rainapp.completerainvalue': {
            'Meta': {'object_name': 'CompleteRainValue'},
            'config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_rainapp.RainappConfig']"}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameterkey': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'lizard_rainapp.geoobject': {
            'Meta': {'object_name': 'GeoObject'},
            'area': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_rainapp.RainappConfig']"}),
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipality_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_rainapp.rainappconfig': {
            'Meta': {'object_name': 'RainappConfig'},
            'filter_id': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jdbcsource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_fewsjdbc.JdbcSource']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'lizard_rainapp.rainvalue': {
            'Meta': {'object_name': 'RainValue'},
            'config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_rainapp.RainappConfig']"}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'geo_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_rainapp.GeoObject']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameterkey': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_rainapp.setting': {
            'Meta': {'object_name': 'Setting', '_ormbases': ['lizard_map.Setting']},
            'setting_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lizard_map.Setting']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['lizard_rainapp']
