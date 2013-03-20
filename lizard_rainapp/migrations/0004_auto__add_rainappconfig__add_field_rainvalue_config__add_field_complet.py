# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ("lizard_fewsjdbc", "0001_initial"),
    )

    def forwards(self, orm):
        db.start_transaction()
        db.clear_table('lizard_rainapp_rainvalue')
        db.clear_table('lizard_rainapp_completerainvalue')
        db.clear_table('lizard_rainapp_geoobject')
        db.commit_transaction()

        # Adding model 'RainappConfig'
        db.create_table('lizard_rainapp_rainappconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('jdbcsource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_fewsjdbc.JdbcSource'])),
            ('filter_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('lizard_rainapp', ['RainappConfig'])

        # Adding field 'RainValue.config'
        db.add_column('lizard_rainapp_rainvalue', 'config', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['lizard_rainapp.RainappConfig']), keep_default=False)

        # Adding field 'CompleteRainValue.config'
        db.add_column('lizard_rainapp_completerainvalue', 'config', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['lizard_rainapp.RainappConfig']), keep_default=False)

        # Deleting field 'GeoObject.filterkey'
        db.delete_column('lizard_rainapp_geoobject', 'filterkey')

        # Adding field 'GeoObject.config'
        db.add_column('lizard_rainapp_geoobject', 'config', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['lizard_rainapp.RainappConfig']), keep_default=False)


    def backwards(self, orm):

        # Deleting model 'RainappConfig'
        db.delete_table('lizard_rainapp_rainappconfig')

        # Deleting field 'RainValue.config'
        db.delete_column('lizard_rainapp_rainvalue', 'config_id')

        # Deleting field 'CompleteRainValue.config'
        db.delete_column('lizard_rainapp_completerainvalue', 'config_id')

        # Adding field 'GeoObject.filterkey'
        db.add_column('lizard_rainapp_geoobject', 'filterkey', self.gf('django.db.models.fields.CharField')(default='', max_length=128), keep_default=False)

        # Deleting field 'GeoObject.config'
        db.delete_column('lizard_rainapp_geoobject', 'config_id')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
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
