"""
JavaScript Exporter

Exports objective mapping data as Miro board JavaScript.
"""

import os
from typing import List, Dict, Any, Optional
from productplan_api_tools.exporters import base


def export_miro(mapping_data: List[Dict[str, Any]], filename: str,
               relationship_config: Optional[Dict[str, List[str]]] = None) -> None:
    """
    Export objective mapping data as Miro JavaScript

    Generates JavaScript code that can be pasted into browser console
    on a Miro board to create objective visualizations.

    Visualization layout:
    - Company objectives: Horizontal row at top (colored shapes)
    - Team objectives: Below each company objective (white boxes with colored headers)
    - Connectors: Lines from company to team objectives

    Args:
        mapping_data: List of mapping dictionaries from ObjectiveMappingResource.fetch_mapping_data()
        filename: Output filename (e.g., "files/objectives.js")
        relationship_config: Optional filtering config
                            Format: {"Company Obj Name": ["Team Obj Name 1", "Team Obj Name 2"]}
                            If None, all relationships from mapping_data are included

    Raises:
        Exception: If file writing fails

    Side effects:
        Creates output directory if needed (via ensure_output_directory)
        Writes JavaScript file to disk
        Prints success message with counts
        Prints warning if data is empty

    JavaScript structure:
        - Async IIFE wrapper
        - Shape creation for company objectives
        - Shape creation for team objectives
        - Connector creation
        - Viewport zoom to fit

    Color scheme:
        - Company objectives: Cycled through 6 colors (red, teal, blue, green, yellow, purple)
        - Team objectives: White background with colored team header
        - Connectors: Match company objective color

    Note:
        Generated code uses Miro Web SDK v2 API
        User must paste into console while on a Miro board
    """
    if not mapping_data:
        print("Warning: No objective data to export")
        return

    print(f"Generating Miro JavaScript for objective visualization: {filename}")

    # Organize data by company objectives
    company_objectives = {}
    team_objectives_by_company = {}

    # First, collect all unique company and team objectives
    for row in mapping_data:
        company_name = row.get('company_objective_name', '')
        company_id = row.get('company_objective_id', '')
        team_name = row.get('team_name', '')
        team_obj_name = row.get('team_objective_name', '')
        team_obj_id = row.get('team_objective_id', '')

        if company_name and company_id:
            company_objectives[company_name] = company_id

            if company_name not in team_objectives_by_company:
                team_objectives_by_company[company_name] = []

            # Only add if we have a relationship (or if no config is provided, add all)
            if relationship_config is None or company_name in relationship_config:
                if relationship_config is None or team_obj_name in relationship_config[company_name]:
                    team_objectives_by_company[company_name].append({
                        'name': team_obj_name,
                        'team': team_name,
                        'id': team_obj_id
                    })

    # Remove duplicates from team objectives
    for company_name in team_objectives_by_company:
        seen = set()
        unique_teams = []
        for team_obj in team_objectives_by_company[company_name]:
            key = (team_obj['name'], team_obj['team'])
            if key not in seen:
                seen.add(key)
                unique_teams.append(team_obj)
        team_objectives_by_company[company_name] = unique_teams

    # Define color scheme for company objectives
    company_colors = [
        {'fill': '#FF6B6B', 'stroke': '#E55252'},  # Red
        {'fill': '#4ECDC4', 'stroke': '#45B7B8'},  # Teal
        {'fill': '#45B7D1', 'stroke': '#3D99C6'},  # Blue
        {'fill': '#96CEB4', 'stroke': '#85BFA3'},  # Green
        {'fill': '#FECA57', 'stroke': '#FDB82F'},  # Yellow
        {'fill': '#A29BFE', 'stroke': '#8A84FF'},  # Purple
    ]

    # Generate JavaScript code
    js_lines = []
    js_lines.append("// ProductPlan Objectives Visualization for Miro")
    js_lines.append("// Generated automatically - paste into browser console on Miro board")
    js_lines.append("// Uses shapes, tables, and connectors for professional visualization")
    js_lines.append("")
    js_lines.append("(async function() {")
    js_lines.append("  console.log('Creating ProductPlan objectives visualization with shapes and connectors...');")
    js_lines.append("")
    js_lines.append("  const shapes = [];")
    js_lines.append("  const connectors = [];")
    js_lines.append("  ")
    js_lines.append("  // Layout configuration")
    js_lines.append("  const startX = 200;")
    js_lines.append("  const companyY = 100;")
    js_lines.append("  const teamStartY = 400;")
    js_lines.append("  const companySpacing = 800;")
    js_lines.append("  const teamSpacing = 350;")
    js_lines.append("  const companyWidth = 400;")
    js_lines.append("  const companyHeight = 120;")
    js_lines.append("  const teamWidth = 300;")
    js_lines.append("  const teamHeight = 100;")
    js_lines.append("")

    for i, (company_name, company_id) in enumerate(company_objectives.items()):
        team_objs = team_objectives_by_company.get(company_name, [])
        color = company_colors[i % len(company_colors)]

        # Calculate positions for this company and its teams
        company_x = f"startX + {i * 800}"

        js_lines.append(f"  // ===== Company Objective {i + 1}: {company_name[:50]}... =====")
        js_lines.append("")

        # Create company objective shape
        escaped_company_name = company_name.replace('`', '\\`').replace('${', '\\${')
        js_lines.append("  // Company Objective Shape")
        js_lines.append("  const companyShape{} = await miro.board.createShape({{".format(i))
        js_lines.append(f"    content: `<p style='font-size:16px; font-weight:bold; text-align:center; margin:8px;'>{escaped_company_name}</p><p style='font-size:12px; text-align:center; color:#666; margin:4px;'>Company Objective</p>`,")
        js_lines.append(f"    shape: 'rectangle',")
        js_lines.append(f"    x: {company_x},")
        js_lines.append(f"    y: companyY,")
        js_lines.append(f"    width: companyWidth,")
        js_lines.append(f"    height: companyHeight,")
        js_lines.append("    style: {")
        js_lines.append(f"      fillColor: '{color['fill']}',")
        js_lines.append(f"      borderColor: '{color['stroke']}',")
        js_lines.append("      borderWidth: 3,")
        js_lines.append("      borderStyle: 'normal',")
        js_lines.append("      borderOpacity: 1.0,")
        js_lines.append("      fillOpacity: 0.9,")
        js_lines.append("      fontFamily: 'arial',")
        js_lines.append("      color: '#FFFFFF',")
        js_lines.append("      textAlign: 'center'")
        js_lines.append("    }")
        js_lines.append("  });")
        js_lines.append(f"  shapes.push(companyShape{i});")
        js_lines.append("")

        # Create team objectives for this company
        if team_objs:
            # Calculate starting position for team objectives (center them under company objective)
            total_team_width = len(team_objs) * 300 + (len(team_objs) - 1) * 50  # teams + spacing
            team_start_x = f"{company_x} - {total_team_width // 2} + {300 // 2}"  # Center align

            for j, team_obj in enumerate(team_objs):
                team_x = f"{team_start_x} + {j * 350}"
                escaped_team_name = team_obj['team'].replace('`', '\\`').replace('${', '\\${')
                escaped_team_objective = team_obj['name'].replace('`', '\\`').replace('${', '\\${')

                js_lines.append(f"  // Team Objective {j + 1} for Company {i + 1}")
                js_lines.append("  const teamShape{}_{} = await miro.board.createShape({{".format(i, j))
                js_lines.append(f"    content: `<p style='font-size:14px; font-weight:bold; text-align:center; margin:4px; background-color:{color['fill']}; color:white; padding:4px; border-radius:3px;'>{escaped_team_name}</p><p style='font-size:11px; text-align:left; margin:6px; line-height:1.3;'>{escaped_team_objective}</p>`,")
                js_lines.append(f"    shape: 'rectangle',")
                js_lines.append(f"    x: {team_x},")
                js_lines.append(f"    y: teamStartY,")
                js_lines.append(f"    width: teamWidth,")
                js_lines.append(f"    height: teamHeight,")
                js_lines.append("    style: {")
                js_lines.append("      fillColor: '#FFFFFF',")
                js_lines.append(f"      borderColor: '{color['stroke']}',")
                js_lines.append("      borderWidth: 2,")
                js_lines.append("      borderStyle: 'normal',")
                js_lines.append("      borderOpacity: 1.0,")
                js_lines.append("      fillOpacity: 1.0,")
                js_lines.append("      fontFamily: 'arial',")
                js_lines.append("      color: '#333333',")
                js_lines.append("      textAlign: 'left'")
                js_lines.append("    }")
                js_lines.append("  });")
                js_lines.append(f"  shapes.push(teamShape{i}_{j});")
                js_lines.append("")

                # Create connector line from company to team objective
                js_lines.append(f"  // Connector from Company {i + 1} to Team {j + 1}")
                js_lines.append("  const connector{}_{} = await miro.board.createConnector({{".format(i, j))
                js_lines.append(f"    start: {{ item: companyShape{i}.id }},")
                js_lines.append(f"    end: {{ item: teamShape{i}_{j}.id }},")
                js_lines.append("    style: {")
                js_lines.append(f"      strokeColor: '{color['stroke']}',")
                js_lines.append("      strokeWidth: 2,")
                js_lines.append("      strokeStyle: 'normal'")
                js_lines.append("    }")
                js_lines.append("  });")
                js_lines.append(f"  connectors.push(connector{i}_{j});")
                js_lines.append("")

    js_lines.append("  console.log(`Created ${shapes.length} shapes and ${connectors.length} connectors`);")
    js_lines.append("  console.log('Objectives visualization complete!');")
    js_lines.append("  ")
    js_lines.append("  // Zoom to fit all content")
    js_lines.append("  await miro.board.viewport.zoomTo([...shapes, ...connectors]);")
    js_lines.append("})();")

    # Write to file
    try:
        # Create parent directory if it doesn't exist
        base.ensure_output_directory(filename)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(js_lines))

        abs_path = os.path.abspath(filename)
        print(f"Miro JavaScript successfully exported to {abs_path}")
        print(f"Generated visualization for {len(company_objectives)} company objectives")

        total_team_objs = sum(len(teams) for teams in team_objectives_by_company.values())
        print(f"Included {total_team_objs} team objectives")
        print("Copy and paste the JavaScript into your browser console while on a Miro board")
    except Exception as e:
        print(f"Error exporting to JavaScript: {e}")
        raise
