# encoding: utf-8

import datetime
import logging
from ckan.common import config, _
import ckan.lib.helpers as h
from six import text_type
from sqlalchemy import Table, select, join, func, and_
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import xlwt as xlrd

import ckan.plugins as p
import ckan.model as model

log = logging.getLogger(__name__)
cache_enabled = p.toolkit.asbool(
    config.get('ckanext.stats.cache_enabled', False)
)

if cache_enabled:
    log.warn(
        'ckanext.stats does not support caching in current implementations'
    )

DATE_FORMAT = '%Y-%m-%d'


def table(name):
    return Table(name, model.meta.metadata, autoload=True)


def datetime2date(datetime_):
    return datetime.date(datetime_.year, datetime_.month, datetime_.day)


class Stats(object):

    @classmethod
    def xloader_tasks(cls):

        eng = create_engine(config.get('sqlalchemy.url'))
        con = eng.connect()

        rs = con.execute(text('SELECT id from "task_status"'))
        rs.fetchone()
        sql = "SELECT  S.entity_id,  R.Name as resourceName, G.title as organizationName, S.state, REPLACE(S.error, 'null', '') as error,  S.last_updated, R.url as url , P.Name as Dataset FROM public.task_status as S"
        sql = sql + " INNER JOIN resource as R ON S.entity_id = R.id "
        sql = sql + " INNER JOIN package as P ON P.id =  R.package_id "
        sql = sql + " INNER JOIN public.group as G ON G.id =  P.owner_org "
        sql = sql + " order by last_updated desc"

        result = con.execute(text(sql))

        names = []
        for row in result:
            names.append(row)

        con.close()

        return names

    @classmethod
    def org_resources(cls):

        eng = create_engine(config.get('sqlalchemy.url'))
        con = eng.connect()

        rs = con.execute(text('SELECT name from "group"'))
        sql = "SELECT * FROM crosstab "
        sql = sql + "($$SELECT G.title as organization, R.format as format, COUNT(*) as ct "
        sql = sql + " FROM resource as R "
        sql = sql + " inner join package as P on R.package_id = P.id "
        sql = sql + ' inner join "group" as G on G.id = P.owner_org '
        sql = sql + " where P.state = 'active' AND R.state = 'active' AND G.state = 'active' "
        sql = sql + " GROUP BY 1,2 "
        sql = sql + " ORDER BY 1,2$$ "
        sql = sql + " ,$$SELECT unnest( "
        sql = sql + " '{CSV, DOC, DOCX, GeoJSON, HTML, JPEG, JSON, PDF, PNG, PPT, PPTX, RSS, TXT, XLS, XLSX, XML, ZIP}'::text[])$$) "
        sql = sql + "  AS final_result "
        sql = sql + ' ("Organization" TEXT, "CSV" bigint, "DOC" bigint, "DOCX" bigint, "GeoJSON" bigint, "HTML" bigint, "JPEG" bigint, "JSON" bigint, "PDF" bigint, "PNG" bigint, "PPT" bigint, "PPTX" bigint, "RSS" bigint, "TXT" bigint, "XLS" bigint, "XLSX" bigint, "XML" bigint, "ZIP" bigint);'

        result = con.execute(text(sql))

        names = []
        for row in result:
            names.append(row)

        con.close()

        return names

    @classmethod
    def path_to_org_resources_file(cls):
        try:
            book = xlrd.Workbook(encoding="utf-8")
            sheet1 = book.add_sheet('sheet1')

            org_resources = Stats.org_resources()

            sheet1.write(0, 0, _('Organization'))
            sheet1.write(0, 1, _('CSV'))
            sheet1.write(0, 2, _('DOC'))
            sheet1.write(0, 3, _('DOCX'))
            sheet1.write(0, 4, _('GeoJSON'))
            sheet1.write(0, 5, _('HTML'))
            sheet1.write(0, 6, _('JPEG'))
            sheet1.write(0, 7, _('JSON'))
            sheet1.write(0, 8, _('PDF'))
            sheet1.write(0, 9, _('PNG'))
            sheet1.write(0, 10, _('PPT'))
            sheet1.write(0, 11, _('PPTX'))
            sheet1.write(0, 12, _('RSS'))
            sheet1.write(0, 13, _('TXT'))
            sheet1.write(0, 14, _('XLS'))
            sheet1.write(0, 15, _('XLSX'))
            sheet1.write(0, 16, _('XML'))
            sheet1.write(0, 17, _('ZIP'))
            for i, e in enumerate(org_resources):
                sheet1.write(i + 1, 0, org_resources[i][0])
                sheet1.write(i + 1, 1, org_resources[i][1])
                sheet1.write(i + 1, 2, org_resources[i][2])
                sheet1.write(i + 1, 3, org_resources[i][3])
                sheet1.write(i + 1, 4, org_resources[i][4])
                sheet1.write(i + 1, 5, org_resources[i][5])
                sheet1.write(i + 1, 6, org_resources[i][6])
                sheet1.write(i + 1, 7, org_resources[i][7])
                sheet1.write(i + 1, 8, org_resources[i][8])
                sheet1.write(i + 1, 9, org_resources[i][9])
                sheet1.write(i + 1, 10, org_resources[i][10])
                sheet1.write(i + 1, 11, org_resources[i][11])
                sheet1.write(i + 1, 12, org_resources[i][12])
                sheet1.write(i + 1, 13, org_resources[i][13])
                sheet1.write(i + 1, 14, org_resources[i][14])
                sheet1.write(i + 1, 15, org_resources[i][15])
                sheet1.write(i + 1, 16, org_resources[i][16])
                sheet1.write(i + 1, 17, org_resources[i][17])
            name = config.get('org_resources_file')
            full_path = config.get('excel_files_directory') + name
            book.save(full_path)
            return name
        except Exception as ex:
            log.info("export_org_resources_to_excel - Error: " + ex.message)
            return None

    @classmethod
    def modified_resources(cls):
        eng = create_engine(config.get('sqlalchemy.url'))
        con = eng.connect()

        rs = con.execute(text('SELECT name from "group"'))
        rs.fetchone()
        sql = 'SELECT G.title as Office, P.name as DataSet, R.Name as resourceName, date(R.last_modified) as last_modified ,date(R.created) as created, R.id, G.name as name, R.url as url  FROM "group" as G INNER JOIN  "package" as P ON G.id = P.owner_org INNER JOIN resource as R ON P.id = R.package_id'
        sql = sql + " WHERE G.type = 'organization' AND G.state = 'active'"
        sql = sql + " ORDER BY created desc,R.last_modified desc"

        result = con.execute(text(sql))

        names = []
        for row in result:
            names.append(row)

        con.close()

        return names

    @classmethod
    def path_to_modified_resources_file(cls):
        try:
            url_max_length = 255
            book = xlrd.Workbook(encoding="utf-8")
            sheet1 = book.add_sheet('sheet1')

            modified_resources = Stats.modified_resources()

            sheet1.write(0, 0, _('Group'))
            sheet1.write(0, 1, _('Dataset'))
            sheet1.write(0, 2, _('Resource'))
            sheet1.write(0, 3, _('Last Modified'))
            sheet1.write(0, 4, _('Created'))
            sheet1.write(0, 5, _('URL'))

            date_format = xlrd.XFStyle()
            date_format.num_format_str = 'dd/mm/yyyy'

            for i, e in enumerate(modified_resources):
                sheet1.write(i + 1, 0, modified_resources[i][0])
                sheet1.write(i + 1, 1, modified_resources[i][1])
                sheet1.write(i + 1, 2, modified_resources[i][2])
                sheet1.write(i + 1, 3, modified_resources[i][3], date_format)
                sheet1.write(i + 1, 4, modified_resources[i][4], date_format)
                if 'http' in modified_resources[i][7] and len(str(modified_resources[i][7])) < url_max_length:
                    sheet1.write(i + 1, 5, xlrd.Formula('HYPERLINK("%s")' % (modified_resources[i][7])))
                else:
                    sheet1.write(i + 1, 5, modified_resources[i][7])

            name = config.get('modified_resources_file')
            full_path = config.get('excel_files_directory') + name
            book.save(full_path)
            return name
        except Exception as ex:
            log.info("export_modified_resources_to_excel Error: " + ex.message)
            return None

    @classmethod
    def path_to_datasets_most_edited_file(cls):
        try:
            book = xlrd.Workbook(encoding="utf-8")
            sheet1 = book.add_sheet('sheet1')

            most_edited_packages = Stats.most_edited_packages()

            sheet1.write(0, 0, _('Dataset'))
            sheet1.write(0, 1, _('Number of edits'))
            for i, e in enumerate(most_edited_packages):
                sheet1.write(i + 1, 0, most_edited_packages[i][0].title)
                sheet1.write(i + 1, 1, most_edited_packages[i][1])

            name = config.get('datasets_most_edited_file')
            full_path = config.get('excel_files_directory') + name
            book.save(full_path)
            return name

        except Exception as ex:
            log.info("export_datasets_most_edited_to_excel - Error: " + ex)
            return None


    @classmethod
    def most_edited_packages(cls, limit=10):
        package_revision = table('package_revision')
        package = table('package')

        s = select([package_revision.c.id, func.count(package_revision.c.revision_id)],
                   from_obj=[package_revision.join(package, package_revision.c.id==package.c.id)]). \
            where(and_(package.c.private == False, package.c.state == 'active', )). \
            group_by(package_revision.c.id). \
            order_by(func.count(package_revision.c.revision_id).desc()). \
            limit(limit)
        res_ids = model.Session.execute(s).fetchall()
        res_pkgs = [(model.Session.query(model.Package).get(text_type(pkg_id)), val) for pkg_id, val in res_ids]
        return res_pkgs

    @classmethod
    def raw_new_datasets(cls):
        new_packages_by_week = RevisionStats.get_by_week('new_packages')
        new_datasets = []
        raw_new_datasets = []
        for week_date, pkgs, num_packages, cumulative_num_packages in new_packages_by_week:
            new_datasets.append('[new Date(%s), %s]' % (week_date.replace('-', ','), num_packages))
            raw_new_datasets.append({'date': h.date_str_to_datetime(week_date), 'new_packages': num_packages})

        return raw_new_datasets

    @classmethod
    def raw_all_package_revisions(cls):
        package_revisions_by_week = RevisionStats.get_by_week('package_revisions')
        all_package_revisions = []
        raw_all_package_revisions = []
        for week_date, revs, num_revisions, cumulative_num_revisions in package_revisions_by_week:
            all_package_revisions.append('[new Date(%s), %s]' % (week_date.replace('-', ','), num_revisions))
            raw_all_package_revisions.append(
                {'date': h.date_str_to_datetime(week_date), 'total_revisions': num_revisions})

        return raw_all_package_revisions

    @classmethod
    def raw_packages_by_week(cls):
        raw_packages_by_week = []
        for (
            week_date, num_packages, cumulative_num_packages
        ) in RevisionStats.get_num_packages_by_week():
            raw_packages_by_week.append({
                u'date': h.date_str_to_datetime(week_date),
                u'total_packages': cumulative_num_packages
            })
        return raw_packages_by_week

    @classmethod
    def top_rated_packages(cls, limit=10):
        # NB Not using sqlalchemy as sqla 0.4 doesn't work using both group_by
        # and apply_avg
        package = table('package')
        rating = table('rating')
        sql = select(
            [
                package.c.id,
                func.avg(rating.c.rating),
                func.count(rating.c.rating)
            ],
            from_obj=[package.join(rating)]
        ).where(and_(package.c.private == False, package.c.state == 'active')
                ).group_by(package.c.id).order_by(
                    func.avg(rating.c.rating).desc(),
                    func.count(rating.c.rating).desc()
                ).limit(limit)
        res_ids = model.Session.execute(sql).fetchall()
        res_pkgs = [(
            model.Session.query(model.Package).get(text_type(pkg_id)), avg, num
        ) for pkg_id, avg, num in res_ids]
        return res_pkgs

    @classmethod
    def largest_groups(cls, limit=10):
        member = table('member')
        package = table('package')

        j = join(member, package, member.c.table_id == package.c.id)

        s = select(
            [member.c.group_id,
             func.count(member.c.table_id)]
        ).select_from(j).group_by(member.c.group_id).where(
            and_(
                member.c.group_id != None, member.c.table_name == 'package',
                package.c.private == False, package.c.state == 'active'
            )
        ).order_by(func.count(member.c.table_id).desc()).limit(limit)

        res_ids = model.Session.execute(s).fetchall()
        res_groups = [
            (model.Session.query(model.Group).get(text_type(group_id)), val)
            for group_id, val in res_ids
        ]
        return res_groups

    @classmethod
    def top_tags(cls, limit=10, returned_tag_info='object'):  # by package
        assert returned_tag_info in ('name', 'id', 'object')
        tag = table('tag')
        package_tag = table('package_tag')
        package = table('package')
        if returned_tag_info == 'name':
            from_obj = [package_tag.join(tag)]
            tag_column = tag.c.name
        else:
            from_obj = None
            tag_column = package_tag.c.tag_id
        j = join(
            package_tag, package, package_tag.c.package_id == package.c.id
        )
        s = select([tag_column,
                    func.count(package_tag.c.package_id)],
                   from_obj=from_obj).select_from(j).where(
                       and_(
                           package_tag.c.state == 'active',
                           package.c.private == False,
                           package.c.state == 'active'
                       )
                   )
        s = s.group_by(tag_column).order_by(
            func.count(package_tag.c.package_id).desc()
        ).limit(limit)
        res_col = model.Session.execute(s).fetchall()
        if returned_tag_info in ('id', 'name'):
            return res_col
        elif returned_tag_info == 'object':
            res_tags = [
                (model.Session.query(model.Tag).get(text_type(tag_id)), val)
                for tag_id, val in res_col
            ]
            return res_tags

    @classmethod
    def top_package_creators(cls, limit=10):
        userid_count = model.Session.query(
            model.Package.creator_user_id,
            func.count(model.Package.creator_user_id)
        ).filter(model.Package.state == 'active'
                 ).filter(model.Package.private == False).group_by(
                     model.Package.creator_user_id
                 ).order_by(func.count(model.Package.creator_user_id).desc()
                            ).limit(limit).all()
        user_count = [
            (model.Session.query(model.User).get(text_type(user_id)), count)
            for user_id, count in userid_count
            if user_id
        ]
        return user_count


class RevisionStats(object):
    @classmethod
    def package_addition_rate(cls, weeks_ago=0):
        week_commenced = cls.get_date_weeks_ago(weeks_ago)
        return cls.get_objects_in_a_week(week_commenced,
                                          type_='package_addition_rate')

    @classmethod
    def package_revision_rate(cls, weeks_ago=0):
        week_commenced = cls.get_date_weeks_ago(weeks_ago)
        return cls.get_objects_in_a_week(week_commenced,
                                          type_='package_revision_rate')

    @classmethod
    def get_date_weeks_ago(cls, weeks_ago):
        '''
        @param weeks_ago: specify how many weeks ago to give count for
                          (0 = this week so far)
        '''
        date_ = datetime.date.today()
        return date_ - datetime.timedelta(days=
                             datetime.date.weekday(date_) + 7 * weeks_ago)

    @classmethod
    def get_week_dates(cls, weeks_ago):
        '''
        @param weeks_ago: specify how many weeks ago to give count for
                          (0 = this week so far)
        '''
        package_revision = table('package_revision')
        revision = table('revision')
        today = datetime.date.today()
        date_from = datetime.datetime(today.year, today.month, today.day) -\
                    datetime.timedelta(days=datetime.date.weekday(today) + \
                                       7 * weeks_ago)
        date_to = date_from + datetime.timedelta(days=7)
        return (date_from, date_to)

    @classmethod
    def get_date_week_started(cls, date_):
        assert isinstance(date_, datetime.date)
        if isinstance(date_, datetime.datetime):
            date_ = datetime2date(date_)
        return date_ - datetime.timedelta(days=datetime.date.weekday(date_))

    @classmethod
    def get_package_revisions(cls):
        '''
        @return: Returns list of revisions and date of them, in
                 format: [(id, date), ...]
        '''
        package_revision = table('package_revision')
        revision = table('revision')
        s = select([package_revision.c.id, revision.c.timestamp], from_obj=[package_revision.join(revision)]).order_by(revision.c.timestamp)
        res = model.Session.execute(s).fetchall() # [(id, datetime), ...]
        return res

    @classmethod
    def get_new_packages(cls):
        '''
        @return: Returns list of new pkgs and date when they were created, in
                 format: [(id, date_ordinal), ...]
        '''
        def new_packages():
            # Can't filter by time in select because 'min' function has to
            # be 'for all time' else you get first revision in the time period.
            package_revision = table('package_revision')
            revision = table('revision')
            s = select([package_revision.c.id, func.min(revision.c.timestamp)], from_obj=[package_revision.join(revision)]).group_by(package_revision.c.id).order_by(func.min(revision.c.timestamp))
            res = model.Session.execute(s).fetchall() # [(id, datetime), ...]
            res_pickleable = []
            for pkg_id, created_datetime in res:
                res_pickleable.append((pkg_id, created_datetime.toordinal()))
            return res_pickleable
        if cache_enabled:
            week_commences = cls.get_date_week_started(datetime.date.today())
            key = 'all_new_packages_%s' + week_commences.strftime(DATE_FORMAT)
            new_packages = our_cache.get_value(key=key,
                                               createfunc=new_packages)
        else:
            new_packages = new_packages()
        return new_packages

    @classmethod
    def get_deleted_packages(cls):
        '''
        @return: Returns list of deleted pkgs and date when they were deleted, in
                 format: [(id, date_ordinal), ...]
        '''
        def deleted_packages():
            # Can't filter by time in select because 'min' function has to
            # be 'for all time' else you get first revision in the time period.
            package_revision = table('package_revision')
            revision = table('revision')
            s = select([package_revision.c.id, func.min(revision.c.timestamp)], from_obj=[package_revision.join(revision)]).\
                where(package_revision.c.state==model.State.DELETED).\
                group_by(package_revision.c.id).\
                order_by(func.min(revision.c.timestamp))
            res = model.Session.execute(s).fetchall() # [(id, datetime), ...]
            res_pickleable = []
            for pkg_id, deleted_datetime in res:
                res_pickleable.append((pkg_id, deleted_datetime.toordinal()))
            return res_pickleable
        if cache_enabled:
            week_commences = cls.get_date_week_started(datetime.date.today())
            key = 'all_deleted_packages_%s' + week_commences.strftime(DATE_FORMAT)
            deleted_packages = our_cache.get_value(key=key,
                                                   createfunc=deleted_packages)
        else:
            deleted_packages = deleted_packages()
        return deleted_packages

    @classmethod
    def get_num_packages_by_week(cls):
        def num_packages():
            new_packages_by_week = cls.get_by_week('new_packages')
            deleted_packages_by_week = cls.get_by_week('deleted_packages')
            first_date = (min(datetime.datetime.strptime(new_packages_by_week[0][0], DATE_FORMAT),
                              datetime.datetime.strptime(deleted_packages_by_week[0][0], DATE_FORMAT))).date()
            cls._cumulative_num_pkgs = 0
            new_pkgs = []
            deleted_pkgs = []
            def build_weekly_stats(week_commences, new_pkg_ids, deleted_pkg_ids):
                num_pkgs = len(new_pkg_ids) - len(deleted_pkg_ids)
                new_pkgs.extend([model.Session.query(model.Package).get(id).name for id in new_pkg_ids])
                deleted_pkgs.extend([model.Session.query(model.Package).get(id).name for id in deleted_pkg_ids])
                cls._cumulative_num_pkgs += num_pkgs
                return (week_commences.strftime(DATE_FORMAT),
                        num_pkgs, cls._cumulative_num_pkgs)
            week_ends = first_date
            today = datetime.date.today()
            new_package_week_index = 0
            deleted_package_week_index = 0
            weekly_numbers = [] # [(week_commences, num_packages, cumulative_num_pkgs])]
            while week_ends <= today:
                week_commences = week_ends
                week_ends = week_commences + datetime.timedelta(days=7)
                if datetime.datetime.strptime(new_packages_by_week[new_package_week_index][0], DATE_FORMAT).date() == week_commences:
                    new_pkg_ids = new_packages_by_week[new_package_week_index][1]
                    new_package_week_index += 1
                else:
                    new_pkg_ids = []
                if datetime.datetime.strptime(deleted_packages_by_week[deleted_package_week_index][0], DATE_FORMAT).date() == week_commences:
                    deleted_pkg_ids = deleted_packages_by_week[deleted_package_week_index][1]
                    deleted_package_week_index += 1
                else:
                    deleted_pkg_ids = []
                weekly_numbers.append(build_weekly_stats(week_commences, new_pkg_ids, deleted_pkg_ids))
            # just check we got to the end of each count
            assert new_package_week_index == len(new_packages_by_week)
            assert deleted_package_week_index == len(deleted_packages_by_week)
            return weekly_numbers
        if cache_enabled:
            week_commences = cls.get_date_week_started(datetime.date.today())
            key = 'number_packages_%s' + week_commences.strftime(DATE_FORMAT)
            num_packages = our_cache.get_value(key=key,
                                               createfunc=num_packages)
        else:
            num_packages = num_packages()
        return num_packages

    @classmethod
    def get_by_week(cls, object_type):
        cls._object_type = object_type
        def objects_by_week():
            if cls._object_type == 'new_packages':
                objects = cls.get_new_packages()
                def get_date(object_date):
                    return datetime.date.fromordinal(object_date)
            elif cls._object_type == 'deleted_packages':
                objects = cls.get_deleted_packages()
                def get_date(object_date):
                    return datetime.date.fromordinal(object_date)
            elif cls._object_type == 'package_revisions':
                objects = cls.get_package_revisions()
                def get_date(object_date):
                    return datetime2date(object_date)
            else:
                raise NotImplementedError()
            first_date = get_date(objects[0][1]) if objects else datetime.date.today()
            week_commences = cls.get_date_week_started(first_date)
            week_ends = week_commences + datetime.timedelta(days=7)
            week_index = 0
            weekly_pkg_ids = [] # [(week_commences, [pkg_id1, pkg_id2, ...])]
            pkg_id_stack = []
            cls._cumulative_num_pkgs = 0
            def build_weekly_stats(week_commences, pkg_ids):
                num_pkgs = len(pkg_ids)
                cls._cumulative_num_pkgs += num_pkgs
                return (week_commences.strftime(DATE_FORMAT),
                        pkg_ids, num_pkgs, cls._cumulative_num_pkgs)
            for pkg_id, date_field in objects:
                date_ = get_date(date_field)
                if date_ >= week_ends:
                    weekly_pkg_ids.append(build_weekly_stats(week_commences, pkg_id_stack))
                    pkg_id_stack = []
                    week_commences = week_ends
                    week_ends = week_commences + datetime.timedelta(days=7)
                pkg_id_stack.append(pkg_id)
            weekly_pkg_ids.append(build_weekly_stats(week_commences, pkg_id_stack))
            today = datetime.date.today()
            while week_ends <= today:
                week_commences = week_ends
                week_ends = week_commences + datetime.timedelta(days=7)
                weekly_pkg_ids.append(build_weekly_stats(week_commences, []))
            return weekly_pkg_ids
        if cache_enabled:
            week_commences = cls.get_date_week_started(datetime.date.today())
            key = '%s_by_week_%s' % (cls._object_type, week_commences.strftime(DATE_FORMAT))
            objects_by_week_ = our_cache.get_value(key=key,
                                    createfunc=objects_by_week)
        else:
            objects_by_week_ = objects_by_week()
        return objects_by_week_

    @classmethod
    def get_objects_in_a_week(cls, date_week_commences,
                                 type_='new-package-rate'):
        '''
        @param type: Specifies what to return about the specified week:
                     "package_addition_rate" number of new packages
                     "package_revision_rate" number of package revisions
                     "new_packages" a list of the packages created
                     in a tuple with the date.
                     "deleted_packages" a list of the packages deleted
                     in a tuple with the date.
        @param dates: date range of interest - a tuple:
                     (start_date, end_date)
        '''
        assert isinstance(date_week_commences, datetime.date)
        if type_ in ('package_addition_rate', 'new_packages'):
            object_type = 'new_packages'
        elif type_ == 'deleted_packages':
            object_type = 'deleted_packages'
        elif type_ == 'package_revision_rate':
            object_type = 'package_revisions'
        else:
            raise NotImplementedError()
        objects_by_week = cls.get_by_week(object_type)
        date_wc_str = date_week_commences.strftime(DATE_FORMAT)
        object_ids = None
        for objects_in_a_week in objects_by_week:
            if objects_in_a_week[0] == date_wc_str:
                object_ids = objects_in_a_week[1]
                break
        if object_ids is None:
            raise TypeError('Week specified is outside range')
        assert isinstance(object_ids, list)
        if type_ in ('package_revision_rate', 'package_addition_rate'):
            return len(object_ids)
        elif type_ in ('new_packages', 'deleted_packages'):
            return [ model.Session.query(model.Package).get(pkg_id) \
                     for pkg_id in object_ids ]
