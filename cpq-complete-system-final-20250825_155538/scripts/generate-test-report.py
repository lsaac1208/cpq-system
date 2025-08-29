#!/usr/bin/env python3
"""
Test Report Generator
生成综合测试报告，包括前端和后端测试结果
"""

import json
import xml.etree.ElementTree as ET
import os
import sys
from datetime import datetime
from pathlib import Path

def parse_junit_xml(junit_file):
    """解析JUnit XML文件"""
    if not os.path.exists(junit_file):
        return None
    
    try:
        tree = ET.parse(junit_file)
        root = tree.getroot()
        
        # 处理不同的根节点格式
        if root.tag == 'testsuites':
            # 如果是 testsuites 根节点，取第一个 testsuite
            testsuite = root.find('testsuite')
            if testsuite is not None:
                root = testsuite
        
        total = int(root.get('tests', 0))
        failures = int(root.get('failures', 0))
        errors = int(root.get('errors', 0))
        skipped = int(root.get('skipped', 0))
        time = float(root.get('time', 0))
        
        return {
            'total': total,
            'passed': total - failures - errors - skipped,
            'failures': failures,
            'errors': errors,
            'skipped': skipped,
            'time': time,
            'success_rate': ((total - failures - errors) / total * 100) if total > 0 else 0
        }
    except Exception as e:
        print(f"Error parsing {junit_file}: {e}")
        return None

def parse_coverage_xml(coverage_file):
    """解析覆盖率XML文件"""
    if not os.path.exists(coverage_file):
        return None
    
    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        # Find coverage element
        coverage_elem = root if root.tag == 'coverage' else root.find('coverage')
        if coverage_elem is not None:
            line_rate = float(coverage_elem.get('line-rate', 0))
            branch_rate = float(coverage_elem.get('branch-rate', 0))
            return {
                'line_coverage': line_rate * 100,
                'branch_coverage': branch_rate * 100
            }
    except Exception as e:
        print(f"Error parsing {coverage_file}: {e}")
        
    return None

def parse_vitest_coverage(coverage_dir):
    """解析Vitest覆盖率报告"""
    coverage_summary_file = os.path.join(coverage_dir, 'coverage-summary.json')
    
    if not os.path.exists(coverage_summary_file):
        return None
    
    try:
        with open(coverage_summary_file, 'r') as f:
            data = json.load(f)
        
        total = data.get('total', {})
        return {
            'line_coverage': total.get('lines', {}).get('pct', 0),
            'branch_coverage': total.get('branches', {}).get('pct', 0),
            'function_coverage': total.get('functions', {}).get('pct', 0),
            'statement_coverage': total.get('statements', {}).get('pct', 0)
        }
    except Exception as e:
        print(f"Error parsing coverage summary: {e}")
        return None

def generate_html_report(backend_results, frontend_results, output_file):
    """生成HTML测试报告"""
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPQ系统测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .card {{ background: white; border: 1px solid #e1e5e9; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h3 {{ margin: 0 0 15px; color: #2c3e50; font-size: 1.2em; }}
        .metric {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
        .metric-label {{ color: #666; }}
        .metric-value {{ font-weight: bold; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .danger {{ color: #e74c3c; }}
        .progress-bar {{ width: 100%; height: 10px; background: #ecf0f1; border-radius: 5px; overflow: hidden; margin: 5px 0; }}
        .progress-fill {{ height: 100%; transition: width 0.3s ease; }}
        .progress-success {{ background: linear-gradient(90deg, #27ae60, #2ecc71); }}
        .progress-warning {{ background: linear-gradient(90deg, #f39c12, #f1c40f); }}
        .progress-danger {{ background: linear-gradient(90deg, #e74c3c, #c0392b); }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .footer {{ text-align: center; padding: 20px; color: #666; border-top: 1px solid #e1e5e9; margin-top: 40px; }}
        .stats {{ display: flex; justify-content: space-around; text-align: center; }}
        .stats > div {{ flex: 1; }}
        .stats .number {{ font-size: 2em; font-weight: bold; }}
        .stats .label {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 CPQ系统测试报告</h1>
            <p>生成时间: {now}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 测试概览</h2>
                <div class="summary">"""

    # 后端测试结果卡片
    if backend_results:
        backend_badge = "badge-success" if backend_results['success_rate'] >= 95 else "badge-warning" if backend_results['success_rate'] >= 80 else "badge-danger"
        coverage_color = "success" if backend_results.get('coverage', {}).get('line_coverage', 0) >= 80 else "warning" if backend_results.get('coverage', {}).get('line_coverage', 0) >= 60 else "danger"
        
        html_content += f"""
                    <div class="card">
                        <h3>🐍 后端测试</h3>
                        <div class="stats">
                            <div>
                                <div class="number success">{backend_results['passed']}</div>
                                <div class="label">通过</div>
                            </div>
                            <div>
                                <div class="number danger">{backend_results['failures'] + backend_results['errors']}</div>
                                <div class="label">失败</div>
                            </div>
                            <div>
                                <div class="number">{backend_results['total']}</div>
                                <div class="label">总计</div>
                            </div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">成功率</span>
                            <span class="metric-value success">{backend_results['success_rate']:.1f}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-success" style="width: {backend_results['success_rate']}%"></div>
                        </div>"""
        
        if 'coverage' in backend_results:
            html_content += f"""
                        <div class="metric">
                            <span class="metric-label">代码覆盖率</span>
                            <span class="metric-value {coverage_color}">{backend_results['coverage']['line_coverage']:.1f}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-{'success' if backend_results['coverage']['line_coverage'] >= 80 else 'warning' if backend_results['coverage']['line_coverage'] >= 60 else 'danger'}" style="width: {backend_results['coverage']['line_coverage']}%"></div>
                        </div>"""
        
        html_content += f"""
                        <div class="metric">
                            <span class="metric-label">执行时间</span>
                            <span class="metric-value">{backend_results['time']:.2f}s</span>
                        </div>
                        <span class="badge {backend_badge}">{"✅ 通过" if backend_results['success_rate'] >= 95 else "⚠️ 警告" if backend_results['success_rate'] >= 80 else "❌ 失败"}</span>
                    </div>"""

    # 前端测试结果卡片
    if frontend_results:
        frontend_badge = "badge-success" if frontend_results['success_rate'] >= 95 else "badge-warning" if frontend_results['success_rate'] >= 80 else "badge-danger"
        frontend_coverage_color = "success" if frontend_results.get('coverage', {}).get('line_coverage', 0) >= 80 else "warning" if frontend_results.get('coverage', {}).get('line_coverage', 0) >= 60 else "danger"
        
        html_content += f"""
                    <div class="card">
                        <h3>⚡ 前端测试</h3>
                        <div class="stats">
                            <div>
                                <div class="number success">{frontend_results['passed']}</div>
                                <div class="label">通过</div>
                            </div>
                            <div>
                                <div class="number danger">{frontend_results['failures'] + frontend_results['errors']}</div>
                                <div class="label">失败</div>
                            </div>
                            <div>
                                <div class="number">{frontend_results['total']}</div>
                                <div class="label">总计</div>
                            </div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">成功率</span>
                            <span class="metric-value success">{frontend_results['success_rate']:.1f}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-success" style="width: {frontend_results['success_rate']}%"></div>
                        </div>"""
        
        if 'coverage' in frontend_results:
            html_content += f"""
                        <div class="metric">
                            <span class="metric-label">代码覆盖率</span>
                            <span class="metric-value {frontend_coverage_color}">{frontend_results['coverage']['line_coverage']:.1f}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-{'success' if frontend_results['coverage']['line_coverage'] >= 80 else 'warning' if frontend_results['coverage']['line_coverage'] >= 60 else 'danger'}" style="width: {frontend_results['coverage']['line_coverage']}%"></div>
                        </div>"""
        
        html_content += f"""
                        <div class="metric">
                            <span class="metric-label">执行时间</span>
                            <span class="metric-value">{frontend_results['time']:.2f}s</span>
                        </div>
                        <span class="badge {frontend_badge}">{"✅ 通过" if frontend_results['success_rate'] >= 95 else "⚠️ 警告" if frontend_results['success_rate'] >= 80 else "❌ 失败"}</span>
                    </div>"""

    # 计算总体状态
    total_tests = (backend_results['total'] if backend_results else 0) + (frontend_results['total'] if frontend_results else 0)
    total_passed = (backend_results['passed'] if backend_results else 0) + (frontend_results['passed'] if frontend_results else 0)
    overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    overall_badge = "badge-success" if overall_rate >= 95 else "badge-warning" if overall_rate >= 80 else "badge-danger"
    
    html_content += f"""
                    <div class="card">
                        <h3>📋 总体状态</h3>
                        <div class="stats">
                            <div>
                                <div class="number success">{total_passed}</div>
                                <div class="label">总通过</div>
                            </div>
                            <div>
                                <div class="number">{total_tests}</div>
                                <div class="label">总测试</div>
                            </div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">整体成功率</span>
                            <span class="metric-value success">{overall_rate:.1f}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-success" style="width: {overall_rate}%"></div>
                        </div>
                        <span class="badge {overall_badge}">{"🎉 优秀" if overall_rate >= 95 else "⚠️ 良好" if overall_rate >= 80 else "❌ 需要改进"}</span>
                    </div>
                </div>
            </div>"""

    # 详细信息部分
    html_content += """
            <div class="section">
                <h2>📝 详细信息</h2>"""
    
    if backend_results:
        html_content += f"""
                <div class="card">
                    <h3>后端测试详情</h3>
                    <ul>
                        <li><strong>总测试数:</strong> {backend_results['total']}</li>
                        <li><strong>通过测试:</strong> {backend_results['passed']}</li>
                        <li><strong>失败测试:</strong> {backend_results['failures']}</li>
                        <li><strong>错误测试:</strong> {backend_results['errors']}</li>
                        <li><strong>跳过测试:</strong> {backend_results['skipped']}</li>
                        <li><strong>执行时间:</strong> {backend_results['time']:.2f}秒</li>"""
        
        if 'coverage' in backend_results:
            html_content += f"""
                        <li><strong>行覆盖率:</strong> {backend_results['coverage']['line_coverage']:.1f}%</li>
                        <li><strong>分支覆盖率:</strong> {backend_results['coverage']['branch_coverage']:.1f}%</li>"""
        
        html_content += """
                    </ul>
                </div>"""
    
    if frontend_results:
        html_content += f"""
                <div class="card">
                    <h3>前端测试详情</h3>
                    <ul>
                        <li><strong>总测试数:</strong> {frontend_results['total']}</li>
                        <li><strong>通过测试:</strong> {frontend_results['passed']}</li>
                        <li><strong>失败测试:</strong> {frontend_results['failures']}</li>
                        <li><strong>错误测试:</strong> {frontend_results['errors']}</li>
                        <li><strong>跳过测试:</strong> {frontend_results['skipped']}</li>
                        <li><strong>执行时间:</strong> {frontend_results['time']:.2f}秒</li>"""
        
        if 'coverage' in frontend_results:
            html_content += f"""
                        <li><strong>行覆盖率:</strong> {frontend_results['coverage']['line_coverage']:.1f}%</li>
                        <li><strong>分支覆盖率:</strong> {frontend_results['coverage']['branch_coverage']:.1f}%</li>
                        <li><strong>函数覆盖率:</strong> {frontend_results['coverage']['function_coverage']:.1f}%</li>
                        <li><strong>语句覆盖率:</strong> {frontend_results['coverage']['statement_coverage']:.1f}%</li>"""
        
        html_content += """
                    </ul>
                </div>"""

    html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>🔧 由CPQ系统CI/CD流水线自动生成</p>
        </div>
    </div>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """主函数"""
    # 设置路径
    base_dir = Path(__file__).parent.parent
    api_dir = base_dir / 'apps' / 'api'
    web_dir = base_dir / 'apps' / 'web'
    
    # 解析后端测试结果
    backend_results = None
    backend_junit = api_dir / 'junit.xml'
    backend_coverage = api_dir / 'coverage.xml'
    
    if backend_junit.exists():
        backend_results = parse_junit_xml(str(backend_junit))
        print(f"后端测试结果: {backend_results}")
        if backend_results and backend_coverage.exists():
            coverage_data = parse_coverage_xml(str(backend_coverage))
            if coverage_data:
                backend_results['coverage'] = coverage_data
    
    # 解析前端测试结果
    frontend_results = None
    frontend_junit = web_dir / 'test-results.xml'
    frontend_coverage_dir = web_dir / 'coverage'
    
    if frontend_junit.exists():
        frontend_results = parse_junit_xml(str(frontend_junit))
        if frontend_results and frontend_coverage_dir.exists():
            coverage_data = parse_vitest_coverage(str(frontend_coverage_dir))
            if coverage_data:
                frontend_results['coverage'] = coverage_data
    
    # 生成报告
    output_file = base_dir / 'test-report.html'
    generate_html_report(backend_results, frontend_results, str(output_file))
    
    print(f"✅ 测试报告已生成: {output_file}")
    
    # 输出简单的控制台摘要
    if backend_results or frontend_results:
        print("\n📊 测试摘要:")
        
        if backend_results:
            print(f"   🐍 后端: {backend_results['passed']}/{backend_results['total']} 通过 ({backend_results['success_rate']:.1f}%)")
            if 'coverage' in backend_results:
                print(f"      📈 覆盖率: {backend_results['coverage']['line_coverage']:.1f}%")
        
        if frontend_results:
            print(f"   ⚡ 前端: {frontend_results['passed']}/{frontend_results['total']} 通过 ({frontend_results['success_rate']:.1f}%)")
            if 'coverage' in frontend_results:
                print(f"      📈 覆盖率: {frontend_results['coverage']['line_coverage']:.1f}%")
        
        # 计算总体状态
        total_tests = (backend_results['total'] if backend_results else 0) + (frontend_results['total'] if frontend_results else 0)
        total_passed = (backend_results['passed'] if backend_results else 0) + (frontend_results['passed'] if frontend_results else 0)
        overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"   🎯 总体: {total_passed}/{total_tests} 通过 ({overall_rate:.1f}%)")
        
        # 设置退出代码
        if overall_rate < 80:
            print("❌ 测试通过率低于80%，流水线标记为失败")
            sys.exit(1)
        elif overall_rate < 95:
            print("⚠️  测试通过率低于95%，需要改进")
        else:
            print("🎉 测试通过率优秀！")
    else:
        print("⚠️  未找到测试结果文件")
        sys.exit(1)

if __name__ == '__main__':
    main()