from collections import OrderedDict

from wazimap.geo import geo_data
from wazimap.data.tables import get_model_from_fields
from wazimap.data.utils import get_session, calculate_median, merge_dicts, get_stat_data, get_objects_by_geo, group_remainder
import logging

# ensure tables are loaded
import janaganana.tables  # noqa

PROFILE_SECTIONS = (
    'demographics',
    'chumma'
)

# Household recodes
COOKING_FUEL_RECODES = OrderedDict([
    ('WOOD', 'Wood'),
    ('LPG', 'LPG'),
    ('GUITHA', 'Guitha'),
    ('BIOGAS', 'Biogas'),
    ('KEROSENE', 'Kerosene'),
    ('ELECTRICITY', 'Electricity'),
    ('OTHERS', 'Others'),
    ('NOT_STATED', 'Not Stated')
])

FOUNDATION_TYPE_RECODES = OrderedDict([
    ('MUD_BONDED', 'Mud Bonded'),
    ('WOODEN_PILLAR', 'Wooden Pillar'),
    ('CEMENT_BONDED', 'Cement Bonded'),
    ('RCC_WITH_PILLAR', 'RCC with Pillar'),
    ('OTHERS', 'Others'),
    ('NOT_STATED', 'Not Stated')
])

OUTER_WALL_TYPE_RECODES = OrderedDict([
    ('MUD_BONDED', 'Mud Bonded'),
    ('CEMENT_BONDED', 'Cement Bonded'),
    ('BAMBOO', 'Bamboo'),
    ('WOOD_PLANKS', 'Wood Planks'),
    ('OTHERS', 'Others'),
    ('NOT_STATED', 'Not Stated'),
    ('UNBACKED_BRICK', 'Unbacked Brick')
])

ROOF_TYPE_RECODES = OrderedDict([
    ('GALV_IRON', 'Galvanized Iron'),
    ('TILE_SLATE', 'Slate'),
    ('RCC', 'Reinforced Concrete'),
    ('THATCH', 'Thatch'),
    ('NOT_STATED', 'Not Stated'),
    ('MUD', 'Mud'),
    ('WOOD_PLANKS', 'Wood Planks'),
    ('OTHERS', 'Others')
])

TOILET_TYPE_RECODES = OrderedDict([
    ('FLUSH_TOILET', 'Flush'),
    ('NO_TOILET', 'None'),
    ('ORDINARY_TOILET', 'Ordinary'),
    ('NOT_STATED', 'Not Stated')
])

DRINKING_WATER_RECODES = OrderedDict([
    ('TAP_PIPED', 'Piped Tap'),
    ('TUBEWELL', 'Tube Well'),
    ('SPOUT_WATER', 'Spout Water'),
    ('UNCOVERED_WELL', 'Uncovered Well'),
    ('COVERED_WELL', 'Covered Well'),
    ('OTHERS', 'Others'),
    ('RIVER_STREAM', 'River or Stream'),
    ('NOT_STATED', 'Not Stated')
])

LIGHTING_FUEL_RECODES = OrderedDict([
    ('ELECTRICITY', 'Electricity'),
    ('KEROSENE', 'Kerosene'),
    ('SOLAR', 'Solar'),
    ('OTHERS', 'Others'),
    ('NOT_STATED', 'Not Stated'),
    ('BIOGAS', 'Biogas')
])

HOME_OWNERSHIP_RECODES = OrderedDict([
    ('OWNED', 'Owned'),
    ('RENTED', 'Rented'),
    ('OTHERS', 'Others'),
    ('INSTITUTIONAL', 'Institutional')
])

# Demographic recodes
DISABILITY_RECODES = OrderedDict([
    ('PHYSICAL', 'Physical'),
    ('BLINDNESS_LOW_VISION', 'Blind/Low Vision'),
    ('DEAF_HEARING', 'Deaf'),
    ('SPEECH_PROBLEM', 'Speech'),
    ('MULTIPLE_DISABILITY', 'Multiple Disabilities'),
    ('MENTAL_DISABILITY', 'Mental Disability'),
    ('INTELLECTUAL_DISABILITY', 'Intellectual'),
    ('DEAF_BLIND', 'Deaf and Blind')
])

# Education recodes
EDUCATION_LEVEL_PASSED_RECODES = OrderedDict([
    ('PRIMARY_1_5', 'Primary'),
    ('LOWER_SECONDARY_6_8', 'Lower Secondary'),
    ('SECONDARY_9_10', 'Secondary'),
    ('SLC_AND_EQUIVALENT', 'SLC'),
    ('INTERMEDIATE', 'Intermed.'),
    ('BEGINNER', 'Beginner'),
    ('NON_FORMAL', 'Non-formal'),
    ('GRADUATE', 'Graduate'),
    ('POST_GRADUATE_AND_ABOVE', 'Post-graduate and Above'),
    ('NOT_STATED', 'Not Stated'),
    ('OTHERS', 'Others')
])

LITERACY_RECODES = OrderedDict([
    ('CAN_READ_WRITE', 'Can Read and Write'),
    ('CANT_READ_WRITE', 'Not Literate'),
    ('CAN_READ_ONLY', 'Can Read'),
    ('NOT_STATED', 'Not Stated')
])

SCHOOL_ATTENDANCE_RECODES = OrderedDict([
    ('SCHOOL_GOING', 'Attending'),
    ('NOT_GOING', 'Not Attending'),
    ('ATTENDENCE_NOT_STATED', 'Not Stated')
])


def get_census_profile(geo_code, geo_level, profile_name=None):
    session = get_session()

    try:
        geo_summary_levels = geo_data.get_summary_geo_info(geo_code, geo_level)
        data = {}

        for section in PROFILE_SECTIONS:
            function_name = 'get_%s_profile' % section
            if function_name in globals():
                func = globals()[function_name]
                data[section] = func(geo_code, geo_level, session)

                # get profiles for province and/or country
                for level, code in geo_summary_levels:
                    # merge summary profile into current geo profile
                    merge_dicts(data[section], func(code, level, session), level)
        return data

    finally:
        session.close()

def get_households_profile(geo_code, geo_level, session):

    # cooking fuel
    cooking_fuel_dict, total_households = get_stat_data(
        'main type of cooking fuel', geo_level, geo_code, session,
        recode=dict(COOKING_FUEL_RECODES),
        key_order=COOKING_FUEL_RECODES.values())
    total_wood = cooking_fuel_dict['Wood']['numerators']['this']

    # foundation type
    foundation_type_dict, _ = get_stat_data(
        'foundation type', geo_level, geo_code, session,
        recode=dict(FOUNDATION_TYPE_RECODES),
        key_order=FOUNDATION_TYPE_RECODES.values())
    total_mud_bonded_foundation = \
        foundation_type_dict['Mud Bonded']['numerators']['this']

    # outer wall type
    outer_wall_type_dict, _ = get_stat_data(
        'outer wall type', geo_level, geo_code, session,
        recode=dict(OUTER_WALL_TYPE_RECODES),
        key_order=OUTER_WALL_TYPE_RECODES.values())
    total_mud_bonded_wall = \
        outer_wall_type_dict['Mud Bonded']['numerators']['this']

    # roof type
    roof_type_dict, _ = get_stat_data(
        'roof type', geo_level, geo_code, session,
        recode=dict(ROOF_TYPE_RECODES),
        key_order=ROOF_TYPE_RECODES.values())
    total_galvanized_roof =\
        roof_type_dict['Galvanized Iron']['numerators']['this']

    # toilet type
    toilet_type_dict, _ = get_stat_data(
        'toilet type', geo_level, geo_code, session,
        recode=dict(TOILET_TYPE_RECODES),
        key_order=TOILET_TYPE_RECODES.values())
    total_flush_toilet = toilet_type_dict['Flush']['numerators']['this']

    # drinking water source
    drinking_water_dict, _ = get_stat_data(
        'drinking water source', geo_level, geo_code, session,
        recode=dict(DRINKING_WATER_RECODES),
        key_order=DRINKING_WATER_RECODES.values())
    total_piped_tap = drinking_water_dict['Piped Tap']['numerators']['this']

    # lighting fuel
    lighting_fuel_dict, _ = get_stat_data(
        'lighting fuel', geo_level, geo_code, session,
        recode=dict(LIGHTING_FUEL_RECODES),
        key_order=LIGHTING_FUEL_RECODES.values())
    total_electricity = lighting_fuel_dict['Electricity']['numerators']['this']

    # home ownership
    home_ownership_dict, _ = get_stat_data(
        'home ownership', geo_level, geo_code, session,
        recode=dict(HOME_OWNERSHIP_RECODES),
        key_order=HOME_OWNERSHIP_RECODES.values())
    total_own_home = home_ownership_dict['Owned']['numerators']['this']

    return {
        'total_households': {
            'name': 'Households',
            'values': {'this': total_households}
        },
        'cooking_fuel_distribution': cooking_fuel_dict,
        'cooking_wood': {
            'name': 'Use wood for cooking',
            'numerators': {'this': total_wood},
            'values': {'this': round(total_wood / total_households * 100, 2)},
        },
        'foundation_type_distribution': foundation_type_dict,
        'mud_bonded_foundation': {
            'name': 'Have a mud-bonded foundation',
            'numerators': {'this': total_mud_bonded_foundation},
            'values':
                {'this': round(
                    total_mud_bonded_foundation / total_households * 100, 2)},
        },
        'outer_wall_type_distribution': outer_wall_type_dict,
        'mud_bonded_wall': {
            'name': 'Have mud-bonded walls',
            'numerators': {'this': total_mud_bonded_wall},
            'values':
                {'this': round(
                    total_mud_bonded_wall / total_households * 100, 2)},
        },
        'roof_type_distribution': roof_type_dict,
        'galvanized_roof': {
            'name': 'Have a galvanized iron roof',
            'numerators': {'this': total_galvanized_roof},
            'values':
                {'this': round(
                    total_galvanized_roof / total_households * 100, 2)},
        },
        'toilet_type_distribution': toilet_type_dict,
        'flush_toilet': {
            'name': 'Have a flush toilet',
            'numerators': {'this': total_flush_toilet},
            'values':
                {'this': round(
                    total_flush_toilet / total_households * 100, 2)},
        },
        'drinking_water_distribution': drinking_water_dict,
        'piped_tap': {
            'name': 'Use piped tap water for drinking',
            'numerators': {'this': total_piped_tap},
            'values':
                {'this': round(
                    total_piped_tap / total_households * 100, 2)},
        },
        'lighting_fuel_distribution': lighting_fuel_dict,
        'lighting_electricity': {
            'name': 'Use electricity for lighting',
            'numerators': {'this': total_electricity},
            'values':
                {'this': round(
                    total_electricity / total_households * 100, 2)},
        },
        'home_ownership_distribution': home_ownership_dict,
        'own_home': {
            'name': 'Own their own home',
            'numerators': {'this': total_own_home},
            'values':
                {'this': round(
                    total_own_home / total_households * 100, 2)},
        }
    }


def get_education_profile(geo_code, geo_level, session):
    edu_level_reached, pop_five_and_older = get_stat_data(
        'education level passed', geo_level, geo_code, session,
        recode=dict(EDUCATION_LEVEL_PASSED_RECODES),
        key_order=EDUCATION_LEVEL_PASSED_RECODES.values())

    total_primary = 0.0
    for key, data in edu_level_reached.iteritems():
        if 'Primary' == key:
            total_primary += data['numerators']['this']

    all_edu_level_by_sex, _ = get_stat_data(
        ['education level passed', 'sex'], geo_level, geo_code, session,
        recode={
            'education level passed': dict(EDUCATION_LEVEL_PASSED_RECODES)},
        key_order={
            'education level passed': EDUCATION_LEVEL_PASSED_RECODES.values(),
            'sex': ['Female', 'Male']},
        percent_grouping=['sex'])

    edu_level_by_sex = {
        'Primary': all_edu_level_by_sex['Primary'],
        'Lower Secondary': all_edu_level_by_sex['Lower Secondary'],
        'Secondary': all_edu_level_by_sex['Secondary'],
        'SLC': all_edu_level_by_sex['SLC'],
        'metadata': all_edu_level_by_sex['metadata']
    }

    total_secondary_by_sex = 0.0
    for data in edu_level_by_sex['Secondary'].itervalues():
        if 'numerators' in data:
            total_secondary_by_sex += data['numerators']['this']

    literacy_by_sex, t_lit = get_stat_data(
        ['literacy', 'sex'], geo_level, geo_code, session,
        recode={'literacy': dict(LITERACY_RECODES)},
        key_order={
            'literacy': LITERACY_RECODES.values(),
            'sex': ['Female', 'Male']},
        percent_grouping=['sex'])

    literacy_dist, _ = get_stat_data(
        'literacy', geo_level, geo_code, session,
        recode=dict(LITERACY_RECODES),
        key_order=LITERACY_RECODES.values())

    school_attendance_by_sex, pop_five_to_twenty_five = get_stat_data(
        ['school attendance', 'sex'], geo_level, geo_code, session,
        recode={'school attendance': dict(SCHOOL_ATTENDANCE_RECODES)},
        key_order={
            'school attendance': SCHOOL_ATTENDANCE_RECODES.values(),
            'sex': ['Female', 'Male']},
        percent_grouping=['sex'])

    school_attendance_dist, _ = get_stat_data(
        'school attendance', geo_level, geo_code, session,
        recode=dict(SCHOOL_ATTENDANCE_RECODES),
        key_order=SCHOOL_ATTENDANCE_RECODES.values())

    education_stats = {
        'aged_five_and_over': {
            'name': 'People Aged 5 and Over',
            'values': {'this': pop_five_and_older}
        },
        'aged_five_to_twenty_five': {
            'name': 'People Aged 5 to 25',
            'values': {'this': pop_five_to_twenty_five}
        },
        'education_level_passed_distribution': edu_level_reached,
        'primary_level_reached': {
            'name': 'Have passed the primary level',
            'numerators': {'this': total_primary},
            'values': {'this': round(total_primary / pop_five_and_older * 100,
                                     2)}
        },
        'education_level_by_sex_distribution': edu_level_by_sex,
        'primary_level_reached_by_sex': {
            'name': 'Have passed the secondary level',
            'numerators': {'this': total_secondary_by_sex},
            'values': {
                'this': round(
                    total_secondary_by_sex / pop_five_and_older * 100,
                    2)}
        },
        'literacy_by_sex_distribution': literacy_by_sex,
        'literacy_distribution': literacy_dist,
        'school_attendance_by_sex_distribution': school_attendance_by_sex,
        'school_attendance_distribution': school_attendance_dist
    }

    return education_stats



POPULATION_SEX_RECODES = OrderedDict([
    ('FEMALE', 'Female'),
    ('MALE', 'Male')
])

POPULATION_AREA_RECODES = OrderedDict([
    ('RURAL', 'Rural'),
    ('URBAN', 'Urban')
])


LITERACY_RECODES = OrderedDict([
    ('LITERATE', 'Literate'),
    ('ILLITERATE', 'Illiterate')
])

def get_demographics_profile(geo_code, geo_level, session):

    population_by_area_dist_data, total_population_by_area = get_stat_data(
        'area', geo_level, geo_code, session,
        recode=dict(POPULATION_AREA_RECODES),
        key_order=POPULATION_AREA_RECODES.values(),
        table_fields=['area', 'sex'])

    population_by_sex_dist_data, _ = get_stat_data(
        'sex', geo_level, geo_code, session,
        recode=dict(POPULATION_SEX_RECODES),
        key_order=POPULATION_SEX_RECODES.values(),
        table_fields=['area', 'sex'])

    literacy_dist_data, _ = get_stat_data(
        'literacy', geo_level, geo_code, session,
        recode=dict(LITERACY_RECODES),
        key_order=LITERACY_RECODES.values(),
        table_fields=['area', 'literacy', 'sex'])

    literacy_by_sex, t_lit = get_stat_data(
        ['sex', 'literacy'], geo_level, geo_code, session,
        table_fields=['area', 'literacy', 'sex'],
        recode={'literacy': dict(LITERACY_RECODES)},
        key_order={'literacy': LITERACY_RECODES.values()},
        percent_grouping=['sex'])

    literacy_by_area, t_lit = get_stat_data(
        ['area', 'literacy'], geo_level, geo_code, session,
        table_fields=['area', 'literacy', 'sex'],
        recode={'area': dict(POPULATION_AREA_RECODES)},
        key_order={'area': POPULATION_AREA_RECODES.values()},
        percent_grouping=['area'])

    final_data = {
        # 'sex_ratio': sex_dist_data,
        'population_area_ratio': population_by_area_dist_data,
        'population_sex_ratio': population_by_sex_dist_data,
        'literacy_by_sex_distribution': literacy_by_sex,
        'literacy_ratio': literacy_dist_data,
        'literacy_by_area_distribution': literacy_by_area,
        'disability_ratio': 123,
        'total_population': {
            "name": "People",
            "values": {"this": total_population_by_area}
        },
        'total_disabled': {
            'name': 'People',
            'values':
                {'this': 111},
        }
    }

    return final_data

def get_chumma_profile(geo_code, geo_level, session):
    final_data = {}
    return final_data