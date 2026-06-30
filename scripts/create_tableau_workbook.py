"""Create a packaged Tableau workbook with cleaned dashboard-ready visuals."""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
TABLEAU_DIR = ROOT / "dashboards" / "tableau"
HYPER_SOURCE = TABLEAU_DIR / "world_cup_analytics.hyper"
TWB_PATH = TABLEAU_DIR / "world_cup_analytics_dashboard.twb"
TWBX_PATH = TABLEAU_DIR / "world_cup_analytics_dashboard.twbx"
FINAL_TWB_PATH = TABLEAU_DIR / "world_cup_analytics_dashboard_final.twb"
FINAL_TWBX_PATH = TABLEAU_DIR / "world_cup_analytics_dashboard_final.twbx"

WORKBOOK_VERSION = "18.1"
NAVY = "#0B2F4A"
PANEL = "#FFFFFF"


def column_xml(
    name: str,
    datatype: str,
    role: str,
    field_type: str,
    aggregation: str | None = None,
    caption: str | None = None,
) -> str:
    aggregation_attr = f" aggregation='{aggregation}'" if aggregation else ""
    caption_attr = f" caption='{escape(caption)}'" if caption else ""
    return (
        f"<column{aggregation_attr}{caption_attr} datatype='{datatype}' name='[{name}]' "
        f"role='{role}' type='{field_type}' />"
    )


def column_instance(column: str, derivation: str, name: str, field_type: str) -> str:
    return (
        f"<column-instance column='[{column}]' derivation='{derivation}' "
        f"name='[{name}]' pivot='key' type='{field_type}' />"
    )


def datasource_xml(caption: str, name: str, table: str, columns: list[str]) -> str:
    return f"""
    <datasource caption='{caption}' inline='true' name='{name}' version='{WORKBOOK_VERSION}'>
      <connection authentication='auth-none' class='hyper' dbname='Data/world_cup_analytics.hyper' default-settings='yes' schema='Extract' sslmode='' tablename='{table}' username='tableau_internal_user'>
        <relation name='{table}' table='[Extract].[{table}]' type='table' />
      </connection>
      <aliases enabled='yes' />
      {chr(10).join(columns)}
      <layout dim-ordering='alphabetic' dim-percentage='0.55' measure-ordering='alphabetic' measure-percentage='0.45' show-structure='true' />
    </datasource>
    """


def worksheet_xml(
    sheet_name: str,
    datasource_caption: str,
    datasource_name: str,
    dependencies: list[str],
    rows: str,
    cols: str,
    mark: str = "Bar",
    color: str | None = None,
    text: str | None = None,
    tooltip: list[str] | None = None,
) -> str:
    encodings = []
    if color:
        encodings.append(f"<color column='{color}' />")
    if text:
        encodings.append(f"<text column='{text}' />")
    for tooltip_field in tooltip or []:
        encodings.append(f"<tooltip column='{tooltip_field}' />")

    return f"""
    <worksheet name='{escape(sheet_name)}'>
      <layout-options>
        <title>
          <formatted-text>
            <run fontcolor='{NAVY}' fontname='Arial' fontsize='15'>{escape(sheet_name)}</run>
          </formatted-text>
        </title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource caption='{escape(datasource_caption)}' name='{datasource_name}' />
          </datasources>
          <datasource-dependencies datasource='{datasource_name}'>
            {chr(10).join(dependencies)}
          </datasource-dependencies>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='worksheet'>
            <format attr='background-color' value='{PANEL}' />
            <format attr='display-field-labels' scope='rows' value='false' />
            <format attr='display-field-labels' scope='cols' value='false' />
          </style-rule>
        </style>
        <panes>
          <pane id='0'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <encodings>
              {chr(10).join(encodings)}
            </encodings>
            <style>
              <style-rule element='mark'>
                <format attr='mark-labels-show' value='true' />
                <format attr='mark-labels-cull' value='true' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>{rows}</rows>
        <cols>{cols}</cols>
      </table>
    </worksheet>
    """


def kpi_datasource(table: str, name: str, caption: str) -> str:
    return datasource_xml(
        caption,
        name,
        table,
        [
            column_xml("kpi_label", "string", "dimension", "nominal"),
            column_xml("kpi_display", "string", "dimension", "nominal"),
            column_xml("kpi_value", "real", "measure", "quantitative", "Avg"),
            column_xml("sort_order", "integer", "dimension", "ordinal"),
        ],
    )


def kpi_sheet(sheet_name: str, datasource_caption: str, datasource_name: str) -> str:
    return worksheet_xml(
        sheet_name,
        datasource_caption,
        datasource_name,
        [
            column_xml("kpi_display", "string", "dimension", "nominal"),
            column_instance("kpi_display", "None", "none:kpi_display:nk", "nominal"),
        ],
        rows="",
        cols="",
        mark="Text",
        text=f"[{datasource_name}].[none:kpi_display:nk]",
    )


def window_xml(name: str, window_class: str = "worksheet") -> str:
    if window_class == "dashboard":
        return f"""
    <window class='dashboard' maximized='true' name='{escape(name)}'>
      <viewpoints>
        <viewpoint name='Matches' />
        <viewpoint name='Teams' />
        <viewpoint name='WC Matches' />
        <viewpoint name='Goals' />
        <viewpoint name='Top Elo' />
        <viewpoint name='Top Scorer' />
        <viewpoint name='Top Goal Scorers' />
        <viewpoint name='Elo Power Ranking' />
        <viewpoint name='Average Goals per Match by World Cup' />
        <viewpoint name='Top World Cup Teams by Points per Match' />
        <viewpoint name='Team Dominance Index' />
      </viewpoints>
      <active id='-1' />
    </window>
    """

    return f"""
    <window class='{window_class}' maximized='true' name='{escape(name)}'>
      <cards>
        <edge name='left'>
          <strip size='180'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='31'><card type='columns' /></strip>
          <strip size='31'><card type='rows' /></strip>
          <strip size='31'><card type='title' /></strip>
        </edge>
      </cards>
      <viewpoint />
    </window>
    """


def build_workbook_xml() -> str:
    kpi_sources = [
        ("kpi_matches", "kpi_matches", "Matches"),
        ("kpi_teams", "kpi_teams", "Teams"),
        ("kpi_world_cup_matches", "kpi_wc_matches", "WC Matches"),
        ("kpi_goals", "kpi_goals", "Goals"),
        ("kpi_top_elo_team", "kpi_top_elo", "Top Elo"),
        ("kpi_top_scorer", "kpi_top_scorer", "Top Scorer"),
    ]

    datasources = [
        *(kpi_datasource(table, name, caption) for table, name, caption in kpi_sources),
        datasource_xml(
            "Top Scorers",
            "scorers",
            "top_scorers_top_10",
            [
                column_xml("scorer_rank", "integer", "dimension", "ordinal"),
                column_xml("scorer_label", "string", "dimension", "nominal"),
                column_xml("scorer", "string", "dimension", "nominal"),
                column_xml("team", "string", "dimension", "nominal"),
                column_xml("goals", "integer", "measure", "quantitative", "Sum", caption="Goals"),
                column_xml("penalties", "integer", "measure", "quantitative", "Sum"),
                column_xml("latest_goal_date", "date", "dimension", "ordinal"),
            ],
        ),
        datasource_xml(
            "Elo Top 10",
            "elo",
            "elo_top_10",
            [
                column_xml("elo_rank", "integer", "dimension", "ordinal"),
                column_xml("elo_label", "string", "dimension", "nominal"),
                column_xml("team", "string", "dimension", "nominal"),
                column_xml("elo_rating", "real", "measure", "quantitative", "Avg", caption="Elo Rating"),
                column_xml("matches_played", "integer", "measure", "quantitative", "Sum"),
                column_xml("wins", "integer", "measure", "quantitative", "Sum"),
                column_xml("goal_difference", "integer", "measure", "quantitative", "Sum"),
            ],
        ),
        datasource_xml(
            "World Cup Scoring Trend",
            "scoring",
            "world_cup_scoring_trend",
            [
                column_xml("world_cup_year", "integer", "dimension", "ordinal"),
                column_xml("matches", "integer", "measure", "quantitative", "Sum"),
                column_xml("total_goals", "integer", "measure", "quantitative", "Sum", caption="Total Goals"),
                column_xml("avg_goals_per_match", "real", "measure", "quantitative", "Avg", caption="Avg Goals"),
            ],
        ),
        datasource_xml(
            "World Cup Points Top 10",
            "wc_points",
            "world_cup_points_top_10",
            [
                column_xml("points_rank", "integer", "dimension", "ordinal"),
                column_xml("points_label", "string", "dimension", "nominal"),
                column_xml("team", "string", "dimension", "nominal"),
                column_xml("matches_played", "integer", "measure", "quantitative", "Sum"),
                column_xml("points", "integer", "measure", "quantitative", "Sum"),
                column_xml("points_per_match", "real", "measure", "quantitative", "Avg", caption="Points per Match"),
                column_xml("win_rate", "real", "measure", "quantitative", "Avg"),
            ],
        ),
        datasource_xml(
            "Team Dominance Top 10",
            "tdi",
            "team_dominance_top_10",
            [
                column_xml("dominance_rank", "integer", "dimension", "ordinal"),
                column_xml("dominance_label", "string", "dimension", "nominal"),
                column_xml("team", "string", "dimension", "nominal"),
                column_xml("matches_played", "integer", "measure", "quantitative", "Sum"),
                column_xml("dominance_index", "real", "measure", "quantitative", "Avg", caption="Dominance Index"),
                column_xml("points_per_match", "real", "measure", "quantitative", "Avg", caption="Points per Match"),
                column_xml("avg_goal_diff", "real", "measure", "quantitative", "Avg"),
            ],
        ),
    ]

    worksheets = [
        *(kpi_sheet(caption, caption, name) for _, name, caption in kpi_sources),
        worksheet_xml(
            "Top Goal Scorers",
            "Top Scorers",
            "scorers",
            [
                column_xml("scorer_label", "string", "dimension", "nominal"),
                column_xml("team", "string", "dimension", "nominal"),
                column_xml("goals", "integer", "measure", "quantitative", "Sum", caption="Goals"),
                column_instance("scorer_label", "None", "none:scorer_label:nk", "nominal"),
                column_instance("team", "None", "none:team:nk", "nominal"),
                column_instance("goals", "Sum", "sum:goals:qk", "quantitative"),
            ],
            rows="[scorers].[none:scorer_label:nk]",
            cols="[scorers].[sum:goals:qk]",
            mark="Bar",
            color="[scorers].[sum:goals:qk]",
            text="[scorers].[sum:goals:qk]",
            tooltip=["[scorers].[none:team:nk]", "[scorers].[sum:goals:qk]"],
        ),
        worksheet_xml(
            "Elo Power Ranking",
            "Elo Top 10",
            "elo",
            [
                column_xml("elo_label", "string", "dimension", "nominal"),
                column_xml("elo_rating", "real", "measure", "quantitative", "Avg", caption="Elo Rating"),
                column_xml("matches_played", "integer", "measure", "quantitative", "Sum"),
                column_xml("wins", "integer", "measure", "quantitative", "Sum"),
                column_instance("elo_label", "None", "none:elo_label:nk", "nominal"),
                column_instance("elo_rating", "Avg", "avg:elo_rating:qk", "quantitative"),
                column_instance("matches_played", "Sum", "sum:matches_played:qk", "quantitative"),
                column_instance("wins", "Sum", "sum:wins:qk", "quantitative"),
            ],
            rows="[elo].[none:elo_label:nk]",
            cols="[elo].[avg:elo_rating:qk]",
            mark="Bar",
            color="[elo].[avg:elo_rating:qk]",
            text="[elo].[avg:elo_rating:qk]",
            tooltip=["[elo].[sum:matches_played:qk]", "[elo].[sum:wins:qk]"],
        ),
        worksheet_xml(
            "Average Goals per Match by World Cup",
            "World Cup Scoring Trend",
            "scoring",
            [
                column_xml("world_cup_year", "integer", "dimension", "ordinal"),
                column_xml("avg_goals_per_match", "real", "measure", "quantitative", "Avg", caption="Avg Goals"),
                column_xml("total_goals", "integer", "measure", "quantitative", "Sum", caption="Total Goals"),
                column_instance("world_cup_year", "None", "none:world_cup_year:ok", "ordinal"),
                column_instance("avg_goals_per_match", "Avg", "avg:avg_goals_per_match:qk", "quantitative"),
                column_instance("total_goals", "Sum", "sum:total_goals:qk", "quantitative"),
            ],
            rows="[scoring].[avg:avg_goals_per_match:qk]",
            cols="[scoring].[none:world_cup_year:ok]",
            mark="Line",
            text="[scoring].[avg:avg_goals_per_match:qk]",
            tooltip=["[scoring].[sum:total_goals:qk]"],
        ),
        worksheet_xml(
            "Top World Cup Teams by Points per Match",
            "World Cup Points Top 10",
            "wc_points",
            [
                column_xml("points_label", "string", "dimension", "nominal"),
                column_xml("points_per_match", "real", "measure", "quantitative", "Avg", caption="Points per Match"),
                column_xml("points", "integer", "measure", "quantitative", "Sum"),
                column_xml("matches_played", "integer", "measure", "quantitative", "Sum"),
                column_instance("points_label", "None", "none:points_label:nk", "nominal"),
                column_instance("points_per_match", "Avg", "avg:points_per_match:qk", "quantitative"),
                column_instance("points", "Sum", "sum:points:qk", "quantitative"),
                column_instance("matches_played", "Sum", "sum:matches_played:qk", "quantitative"),
            ],
            rows="[wc_points].[none:points_label:nk]",
            cols="[wc_points].[avg:points_per_match:qk]",
            mark="Bar",
            color="[wc_points].[avg:points_per_match:qk]",
            text="[wc_points].[avg:points_per_match:qk]",
            tooltip=["[wc_points].[sum:points:qk]", "[wc_points].[sum:matches_played:qk]"],
        ),
        worksheet_xml(
            "Team Dominance Index",
            "Team Dominance Top 10",
            "tdi",
            [
                column_xml("dominance_label", "string", "dimension", "nominal"),
                column_xml("dominance_index", "real", "measure", "quantitative", "Avg", caption="Dominance Index"),
                column_xml("points_per_match", "real", "measure", "quantitative", "Avg", caption="Points per Match"),
                column_xml("avg_goal_diff", "real", "measure", "quantitative", "Avg"),
                column_instance("dominance_label", "None", "none:dominance_label:nk", "nominal"),
                column_instance("dominance_index", "Avg", "avg:dominance_index:qk", "quantitative"),
                column_instance("points_per_match", "Avg", "avg:points_per_match:qk", "quantitative"),
                column_instance("avg_goal_diff", "Avg", "avg:avg_goal_diff:qk", "quantitative"),
            ],
            rows="[tdi].[none:dominance_label:nk]",
            cols="[tdi].[avg:dominance_index:qk]",
            mark="Bar",
            color="[tdi].[avg:dominance_index:qk]",
            text="[tdi].[avg:dominance_index:qk]",
            tooltip=["[tdi].[avg:points_per_match:qk]", "[tdi].[avg:avg_goal_diff:qk]"],
        ),
    ]

    dashboard = """
    <dashboard name='World Cup Analytics'>
      <layout-options>
        <title>
          <formatted-text>
            <run fontcolor='#0B2F4A' fontname='Arial' fontsize='28'>World Cup Analytics Dashboard</run>
            <run fontcolor='#52616B' fontname='Arial' fontsize='10'> Comparing scoring leaders, team strength, World Cup performance, and dominance trends</run>
          </formatted-text>
        </title>
      </layout-options>
      <style>
        <style-rule element='dashboard'>
          <format attr='background-color' value='#F7F9FB' />
        </style-rule>
      </style>
      <size maxheight='950' maxwidth='1300' minheight='950' minwidth='1300' />
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='8000' id='2' type-v2='title' w='100000' x='0' y='0' />
          <zone h='16000' id='3' name='Matches' show-title='true' w='12500' x='0' y='8000' />
          <zone h='16000' id='4' name='Teams' show-title='true' w='12500' x='12500' y='8000' />
          <zone h='16000' id='5' name='WC Matches' show-title='true' w='12500' x='25000' y='8000' />
          <zone h='16000' id='6' name='Goals' show-title='true' w='12500' x='37500' y='8000' />
          <zone h='16000' id='7' name='Top Elo' show-title='true' w='25000' x='50000' y='8000' />
          <zone h='16000' id='8' name='Top Scorer' show-title='true' w='25000' x='75000' y='8000' />
          <zone h='38000' id='9' name='Top Goal Scorers' show-title='true' w='50000' x='0' y='24000' />
          <zone h='38000' id='10' name='Elo Power Ranking' show-title='true' w='50000' x='50000' y='24000' />
          <zone h='38000' id='11' name='Average Goals per Match by World Cup' show-title='true' w='33333' x='0' y='62000' />
          <zone h='38000' id='12' name='Top World Cup Teams by Points per Match' show-title='true' w='33333' x='33333' y='62000' />
          <zone h='38000' id='13' name='Team Dominance Index' show-title='true' w='33334' x='66666' y='62000' />
        </zone>
      </zones>
    </dashboard>
    """

    sheet_names = [
        "Matches",
        "Teams",
        "WC Matches",
        "Goals",
        "Top Elo",
        "Top Scorer",
        "Top Goal Scorers",
        "Elo Power Ranking",
        "Average Goals per Match by World Cup",
        "Top World Cup Teams by Points per Match",
        "Team Dominance Index",
    ]
    windows = [window_xml("World Cup Analytics", "dashboard")] + [
        window_xml(name) for name in sheet_names
    ]

    return dedent(
        f"""\
        <?xml version='1.0' encoding='utf-8' ?>
        <workbook locale='en_US' source-build='0.0.0 (0000.0.0.0)' source-platform='mac' version='{WORKBOOK_VERSION}' xmlns:user='http://www.tableausoftware.com/xml/user'>
          <preferences>
            <preference name='ui.encoding.shelf.height' value='24' />
            <preference name='ui.shelf.height' value='26' />
          </preferences>
          <style-theme name='smooth' />
          <datasources>
            {''.join(datasources)}
          </datasources>
          <worksheets>
            {''.join(worksheets)}
          </worksheets>
          <dashboards>
            {dashboard}
          </dashboards>
          <windows source-height='32'>
            {''.join(windows)}
          </windows>
        </workbook>
        """
    )


def main() -> None:
    if not HYPER_SOURCE.exists():
        raise FileNotFoundError(f"Missing Hyper extract: {HYPER_SOURCE}")

    workbook_xml = build_workbook_xml()
    TWB_PATH.write_text(workbook_xml.lstrip(), encoding="utf-8")
    FINAL_TWB_PATH.write_text(workbook_xml.lstrip(), encoding="utf-8")

    for twbx_path, twb_path in [
        (TWBX_PATH, TWB_PATH),
        (FINAL_TWBX_PATH, FINAL_TWB_PATH),
    ]:
        if twbx_path.exists():
            twbx_path.unlink()
        with ZipFile(twbx_path, "w", ZIP_DEFLATED) as package:
            package.write(twb_path, twb_path.name)
            package.write(HYPER_SOURCE, "Data/world_cup_analytics.hyper")

    print(f"Created {TWB_PATH.relative_to(ROOT)}")
    print(f"Created {TWBX_PATH.relative_to(ROOT)}")
    print(f"Created {FINAL_TWB_PATH.relative_to(ROOT)}")
    print(f"Created {FINAL_TWBX_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
