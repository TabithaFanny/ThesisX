"""
formula_dialog.py — 公式选择对话框

显示常用数学公式分类列表，点击即可插入到文档中。
公式使用 LaTeX 语法（$...$  /  $$...$$）。
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ------------------------------------------------------------------
# 公式数据：(显示名, 预览文本, 插入到文档的 LaTeX)
# ------------------------------------------------------------------

_FORMULAS = {
    "基础运算": [
        ("分数", "a/b", "$\\frac{a}{b}$"),
        ("平方根", "√x", "$\\sqrt{x}$"),
        ("n次根", "ⁿ√x", "$\\sqrt[n]{x}$"),
        ("上标/幂", "x²", "$x^{2}$"),
        ("下标", "xₙ", "$x_{n}$"),
        ("上下标", "xₙ²", "$x_{n}^{2}$"),
        ("绝对值", "|x|", "$|x|$"),
        ("加减号", "±", "$\\pm$"),
        ("乘号", "×", "$\\times$"),
        ("除号", "÷", "$\\div$"),
        ("不等于", "≠", "$\\neq$"),
        ("约等于", "≈", "$\\approx$"),
    ],
    "希腊字母": [
        ("α alpha", "α", "$\\alpha$"),
        ("β beta", "β", "$\\beta$"),
        ("γ gamma", "γ", "$\\gamma$"),
        ("δ delta", "δ", "$\\delta$"),
        ("ε epsilon", "ε", "$\\epsilon$"),
        ("θ theta", "θ", "$\\theta$"),
        ("λ lambda", "λ", "$\\lambda$"),
        ("μ mu", "μ", "$\\mu$"),
        ("π pi", "π", "$\\pi$"),
        ("σ sigma", "σ", "$\\sigma$"),
        ("φ phi", "φ", "$\\varphi$"),
        ("ω omega", "ω", "$\\omega$"),
        ("Δ Delta", "Δ", "$\\Delta$"),
        ("Σ Sigma", "Σ", "$\\Sigma$"),
        ("Ω Omega", "Ω", "$\\Omega$"),
    ],
    "求和与积分": [
        ("求和 Σ", "Σᵢ₌₁ⁿ", "$$\\sum_{i=1}^{n} a_i$$"),
        ("连乘 Π", "Πᵢ₌₁ⁿ", "$$\\prod_{i=1}^{n} a_i$$"),
        ("定积分", "∫ₐᵇ", "$$\\int_{a}^{b} f(x) \\, dx$$"),
        ("不定积分", "∫ f(x)dx", "$$\\int f(x) \\, dx$$"),
        ("二重积分", "∬", "$$\\iint_{D} f(x,y) \\, dx \\, dy$$"),
        ("极限", "lim", "$$\\lim_{x \\to \\infty} f(x)$$"),
        ("极限趋近0", "lim→0", "$$\\lim_{x \\to 0} f(x)$$"),
    ],
    "矩阵与方程组": [
        ("2×2 矩阵", "[ ]₂ₓ₂", "$$\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$$"),
        (
            "3×3 矩阵",
            "[ ]₃ₓ₃",
            "$$\\begin{pmatrix} a & b & c \\\\ d & e & f \\\\ g & h & i \\end{pmatrix}$$",
        ),
        ("行列式", "|A|", "$$\\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix}$$"),
        ("方程组", "{ 方程组", "$$\\begin{cases} x + y = 1 \\\\ x - y = 0 \\end{cases}$$"),
        (
            "分段函数",
            "f(x)=",
            "$$f(x) = \\begin{cases} x^2, & x \\geq 0 \\\\ -x, & x < 0 \\end{cases}$$",
        ),
    ],
    "关系与逻辑": [
        ("大于等于", "≥", "$\\geq$"),
        ("小于等于", "≤", "$\\leq$"),
        ("远大于", "≫", "$\\gg$"),
        ("远小于", "≪", "$\\ll$"),
        ("属于", "∈", "$\\in$"),
        ("不属于", "∉", "$\\notin$"),
        ("子集", "⊂", "$\\subset$"),
        ("交集", "∩", "$\\cap$"),
        ("并集", "∪", "$\\cup$"),
        ("任意", "∀", "$\\forall$"),
        ("存在", "∃", "$\\exists$"),
        ("因此", "∴", "$\\therefore$"),
        ("因为", "∵", "$\\because$"),
        ("正比于", "∝", "$\\propto$"),
        ("无穷", "∞", "$\\infty$"),
    ],
    "常用公式": [
        ("二次公式", "x = −b±√Δ / 2a", "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$"),
        ("勾股定理", "a²+b²=c²", "$$a^{2} + b^{2} = c^{2}$$"),
        ("欧拉公式", "eⁱᶶ = cosθ + isinθ", "$$e^{i\\theta} = \\cos\\theta + i\\sin\\theta$$"),
        ("二项式定理", "(a+b)ⁿ", "$$( a + b )^n = \\sum_{k=0}^{n} \\binom{n}{k} a^{n-k} b^{k}$$"),
        (
            "泰勒展开",
            "f(x) = Σ ...",
            "$$f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(a)}{n!}(x-a)^n$$",
        ),
        ("导数定义", "f'(x) = lim", "$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$"),
        (
            "正态分布",
            "N(μ,σ²)",
            "$$f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}$$",
        ),
        ("贝叶斯公式", "P(A|B)", "$$P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}$$"),
    ],
    "微积分": [
        ("偏导数", "∂f/∂x", "$$\\frac{\\partial f}{\\partial x}$$"),
        ("高阶偏导", "∂²f/∂x²", "$$\\frac{\\partial^{2} f}{\\partial x^{2}}$$"),
        ("混合偏导", "∂²f/∂x∂y", "$$\\frac{\\partial^{2} f}{\\partial x \\partial y}$$"),
        (
            "梯度",
            "∇f",
            "$$\\nabla f = \\left( \\frac{\\partial f}{\\partial x}, \\frac{\\partial f}{\\partial y}, \\frac{\\partial f}{\\partial z} \\right)$$",
        ),
        (
            "散度",
            "∇·F",
            "$$\\nabla \\cdot \\mathbf{F} = \\frac{\\partial F_x}{\\partial x} + \\frac{\\partial F_y}{\\partial y} + \\frac{\\partial F_z}{\\partial z}$$",
        ),
        ("旋度", "∇×F", "$$\\nabla \\times \\mathbf{F}$$"),
        (
            "拉普拉斯算子",
            "∇²f",
            "$$\\nabla^{2} f = \\frac{\\partial^{2} f}{\\partial x^{2}} + \\frac{\\partial^{2} f}{\\partial y^{2}} + \\frac{\\partial^{2} f}{\\partial z^{2}}$$",
        ),
        ("曲线积分", "∫₂ F·ds", "$$\\oint_{C} \\mathbf{F} \\cdot d\\mathbf{s}$$"),
        ("曲面积分", "∬₂ F·dS", "$$\\iint_{S} \\mathbf{F} \\cdot d\\mathbf{S}$$"),
        ("三重积分", "∭", "$$\\iiint_{V} f(x,y,z) \\, dV$$"),
        (
            "格林公式",
            "Green",
            "$$\\oint_{C} (P\\,dx + Q\\,dy) = \\iint_{D} \\left( \\frac{\\partial Q}{\\partial x} - \\frac{\\partial P}{\\partial y} \\right) dA$$",
        ),
        (
            "斯托克斯公式",
            "Stokes",
            "$$\\oint_{C} \\mathbf{F} \\cdot d\\mathbf{r} = \\iint_{S} (\\nabla \\times \\mathbf{F}) \\cdot d\\mathbf{S}$$",
        ),
    ],
    "线性代数": [
        ("转置矩阵", "Aᵀ", "$$A^{T}$$"),
        ("逆矩阵", "A⁻¹", "$$A^{-1}$$"),
        ("矩阵乘法", "AB", "$$C_{ij} = \\sum_{k=1}^{n} A_{ik} B_{kj}$$"),
        ("特征值", "Av = λv", "$$A\\mathbf{v} = \\lambda \\mathbf{v}$$"),
        ("特征方程", "det(A-λI)=0", "$$\\det(A - \\lambda I) = 0$$"),
        ("迹", "tr(A)", "$$\\text{tr}(A) = \\sum_{i=1}^{n} a_{ii}$$"),
        (
            "内积",
            "⟨u,v⟩",
            "$$\\langle \\mathbf{u}, \\mathbf{v} \\rangle = \\sum_{i=1}^{n} u_i v_i$$",
        ),
        ("范数", "‖x‖", "$$\\| \\mathbf{x} \\| = \\sqrt{\\sum_{i=1}^{n} x_i^{2}}$$"),
        (
            "叉积",
            "a×b",
            "$$\\mathbf{a} \\times \\mathbf{b} = \\begin{vmatrix} \\mathbf{i} & \\mathbf{j} & \\mathbf{k} \\\\ a_1 & a_2 & a_3 \\\\ b_1 & b_2 & b_3 \\end{vmatrix}$$",
        ),
        ("克拉默法则", "Cramer", "$$x_i = \\frac{\\det(A_i)}{\\det(A)}$$"),
    ],
    "概率统计": [
        ("期望", "E(X)", "$$E(X) = \\sum_{i} x_i \\, P(X = x_i)$$"),
        ("连续期望", "E(X) ∫", "$$E(X) = \\int_{-\\infty}^{\\infty} x \\, f(x) \\, dx$$"),
        ("方差", "Var(X)", "$$\\text{Var}(X) = E[(X - \\mu)^{2}] = E(X^2) - [E(X)]^2$$"),
        ("协方差", "Cov(X,Y)", "$$\\text{Cov}(X,Y) = E[(X-\\mu_X)(Y-\\mu_Y)]$$"),
        ("相关系数", "ρ(X,Y)", "$$\\rho_{XY} = \\frac{\\text{Cov}(X,Y)}{\\sigma_X \\sigma_Y}$$"),
        ("条件概率", "P(A|B)", "$$P(A|B) = \\frac{P(A \\cap B)}{P(B)}$$"),
        ("全概率公式", "P(A)=Σ", "$$P(A) = \\sum_{i=1}^{n} P(A|B_i) \\, P(B_i)$$"),
        ("二项分布", "B(n,p)", "$$P(X=k) = \\binom{n}{k} p^k (1-p)^{n-k}$$"),
        ("泊松分布", "Poisson", "$$P(X=k) = \\frac{\\lambda^k e^{-\\lambda}}{k!}$$"),
        ("卡方检验", "χ²", "$$\\chi^2 = \\sum_{i=1}^{n} \\frac{(O_i - E_i)^2}{E_i}$$"),
        ("t 检验", "t", "$$t = \\frac{\\bar{X} - \\mu_0}{S / \\sqrt{n}}$$"),
        ("F 检验", "F", "$$F = \\frac{S_1^2}{S_2^2}$$"),
        ("样本均值", "x̄", "$$\\bar{x} = \\frac{1}{n} \\sum_{i=1}^{n} x_i$$"),
        ("样本方差", "s²", "$$s^2 = \\frac{1}{n-1} \\sum_{i=1}^{n} (x_i - \\bar{x})^2$$"),
        ("置信区间", "CI", "$$\\bar{x} \\pm z_{\\alpha/2} \\frac{\\sigma}{\\sqrt{n}}$$"),
    ],
    "微分方程": [
        ("一阶ODE", "dy/dx = f(x)", "$$\\frac{dy}{dx} = f(x, y)$$"),
        ("二阶ODE", "y'' + py' + qy = 0", "$$\\frac{d^{2}y}{dx^{2}} + p\\frac{dy}{dx} + qy = 0$$"),
        (
            "热传导方程",
            "u_t = k u_xx",
            "$$\\frac{\\partial u}{\\partial t} = k \\frac{\\partial^{2} u}{\\partial x^{2}}$$",
        ),
        (
            "波动方程",
            "u_tt = c² u_xx",
            "$$\\frac{\\partial^{2} u}{\\partial t^{2}} = c^{2} \\frac{\\partial^{2} u}{\\partial x^{2}}$$",
        ),
        (
            "拉普拉斯方程",
            "∇²u = 0",
            "$$\\nabla^{2} u = \\frac{\\partial^{2} u}{\\partial x^{2}} + \\frac{\\partial^{2} u}{\\partial y^{2}} = 0$$",
        ),
        (
            "薛定谔方程",
            "iħ ∂ψ/∂t",
            "$$i\\hbar \\frac{\\partial \\psi}{\\partial t} = \\hat{H} \\psi$$",
        ),
        ("约化复形式", "dx/dt = Ax", "$$\\frac{d\\mathbf{x}}{dt} = A\\mathbf{x}$$"),
    ],
    "信号与变换": [
        (
            "傅里叶变换",
            "F(ω)",
            "$$F(\\omega) = \\int_{-\\infty}^{\\infty} f(t) \\, e^{-i\\omega t} \\, dt$$",
        ),
        (
            "傅里叶逆变换",
            "f(t)",
            "$$f(t) = \\frac{1}{2\\pi} \\int_{-\\infty}^{\\infty} F(\\omega) \\, e^{i\\omega t} \\, d\\omega$$",
        ),
        (
            "拉普拉斯变换",
            "L{f}",
            "$$F(s) = \\mathcal{L}\\{f(t)\\} = \\int_{0}^{\\infty} f(t) \\, e^{-st} \\, dt$$",
        ),
        ("Z 变换", "Z{x[n]}", "$$X(z) = \\sum_{n=0}^{\\infty} x[n] \\, z^{-n}$$"),
        (
            "卷积",
            "f*g",
            "$$(f * g)(t) = \\int_{-\\infty}^{\\infty} f(\\tau) \\, g(t - \\tau) \\, d\\tau$$",
        ),
        ("离散傅里叶", "DFT", "$$X[k] = \\sum_{n=0}^{N-1} x[n] \\, e^{-i 2\\pi k n / N}$$"),
    ],
    "优化与机器学习": [
        (
            "梯度下降",
            "θ := θ - α∇J",
            "$$\\theta := \\theta - \\alpha \\nabla_{\\theta} J(\\theta)$$",
        ),
        (
            "损失函数 MSE",
            "MSE",
            "$$\\text{MSE} = \\frac{1}{n} \\sum_{i=1}^{n} (y_i - \\hat{y}_i)^2$$",
        ),
        ("交叉熵", "Cross-Entropy", "$$H(p,q) = -\\sum_{i} p_i \\log q_i$$"),
        (
            "Softmax",
            "softmax",
            "$$\\text{softmax}(z_i) = \\frac{e^{z_i}}{\\sum_{j=1}^{K} e^{z_j}}$$",
        ),
        ("Sigmoid", "σ(x)", "$$\\sigma(x) = \\frac{1}{1 + e^{-x}}$$"),
        ("ReLU", "ReLU", "$$\\text{ReLU}(x) = \\max(0, x)$$"),
        (
            "正则化 L2",
            "L2 reg",
            "$$J(\\theta) = L(\\theta) + \\frac{\\lambda}{2} \\| \\theta \\|^2$$",
        ),
        ("正则化 L1", "L1 reg", "$$J(\\theta) = L(\\theta) + \\lambda \\| \\theta \\|_1$$"),
        (
            "KL 散度",
            "KL(p‖q)",
            "$$D_{\\text{KL}}(p \\| q) = \\sum_{i} p_i \\log \\frac{p_i}{q_i}$$",
        ),
        (
            "注意力机制",
            "Attention",
            "$$\\text{Attention}(Q,K,V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right) V$$",
        ),
        ("信息熵", "H(X)", "$$H(X) = -\\sum_{i} p(x_i) \\log p(x_i)$$"),
        (
            "贝叶斯公式全",
            "Bayes full",
            "$$P(\\theta | D) = \\frac{P(D | \\theta) \\, P(\\theta)}{P(D)}$$",
        ),
    ],
    "物理公式": [
        ("牛顿第二定律", "F = ma", "$$F = ma$$"),
        ("万有引力", "F = Gm₁m₂/r²", "$$F = G \\frac{m_1 m_2}{r^2}$$"),
        ("动能", "E_k", "$$E_k = \\frac{1}{2} m v^{2}$$"),
        ("质能方程", "E = mc²", "$$E = mc^{2}$$"),
        (
            "麦克斯韦方程组",
            "Maxwell",
            "$$\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\epsilon_0}$$",
        ),
        ("波动方程通式", "ψ(x,t)", "$$\\psi(x,t) = A \\sin(kx - \\omega t + \\varphi)$$"),
        ("理想气体", "PV = nRT", "$$PV = nRT$$"),
        ("玄学函数数定义", "Z", "$$Z = \\sum_{i} e^{-\\beta E_i}$$"),
        ("玄学的内能", "U", "$$U = -\\frac{\\partial \\ln Z}{\\partial \\beta}$$"),
    ],
    "化学公式": [
        ("化学反应箭头", "→", "$\\rightarrow$"),
        ("可逆反应", "⇌", "$\\rightleftharpoons$"),
        ("平衡常数", "K_eq", "$$K_{eq} = \\frac{[C]^c [D]^d}{[A]^a [B]^b}$$"),
        ("吉布斯自由能", "ΔG", "$$\\Delta G = \\Delta H - T \\Delta S$$"),
        ("能斯特方程", "Nernst", "$$E = E^{\\circ} - \\frac{RT}{nF} \\ln Q$$"),
        ("阿伦尼乌斯方程", "Arrhenius", "$$k = A \\, e^{-E_a / (RT)}$$"),
        ("摩尔分数", "x_A", "$$x_A = \\frac{n_A}{n_A + n_B}$$"),
        ("pH 定义", "pH", "$$\\text{pH} = -\\log_{10} [\\text{H}^+]$$"),
    ],
}


# ------------------------------------------------------------------
# 公式卡片 Widget
# ------------------------------------------------------------------


class _FormulaCard(QFrame):
    """单个公式卡片：显示名称和预览，点击发射信号。"""

    clicked = pyqtSignal(str)  # 发射要插入的 LaTeX 文本

    def __init__(self, name: str, preview: str, latex: str, parent=None):
        super().__init__(parent)
        self._latex = latex
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(62)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            _FormulaCard {
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            _FormulaCard:hover {
                background: #e8f4fd;
                border-color: #4A90D9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        preview_label = QLabel(preview)
        preview_label.setFont(QFont("Cambria Math", 14))
        preview_label.setStyleSheet("color: #222; background: transparent;")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preview_label)

        name_label = QLabel(name)
        name_label.setFont(QFont("PingFang SC", 9))
        name_label.setStyleSheet("color: #888; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._latex)
        super().mousePressEvent(event)


# ------------------------------------------------------------------
# 公式对话框
# ------------------------------------------------------------------


class FormulaDialog(QDialog):
    """公式选择对话框，点击公式卡片后返回对应 LaTeX 文本。"""

    formula_selected = pyqtSignal(str)  # 选中的 LaTeX 文本

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("插入公式")
        self.setMinimumSize(640, 520)
        self.resize(720, 580)
        self._selected_latex = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 搜索框
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 搜索公式...")
        self._search.setFont(QFont("PingFang SC", 11))
        self._search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #4A90D9; }
        """)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        # Tab widget for categories
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; border-radius: 4px; }
            QTabBar::tab {
                padding: 6px 14px;
                margin-right: 2px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background: #f5f5f5;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #4A90D9;
                font-weight: bold;
            }
            QTabBar::tab:hover { background: #e8f4fd; }
        """)
        self._tabs.setUsesScrollButtons(True)
        layout.addWidget(self._tabs)

        self._all_cards = []  # list of (_FormulaCard, category_name, formula_name)

        for category, formulas in _FORMULAS.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("QScrollArea { background: white; }")

            container = QWidget()
            grid = QGridLayout(container)
            grid.setContentsMargins(8, 8, 8, 8)
            grid.setSpacing(8)

            for idx, (name, preview, latex) in enumerate(formulas):
                card = _FormulaCard(name, preview, latex)
                card.clicked.connect(self._on_formula_clicked)
                row, col = divmod(idx, 3)
                grid.addWidget(card, row, col)
                self._all_cards.append((card, category, name))

            # fill remaining cells in last row for alignment
            remainder = len(formulas) % 3
            if remainder:
                for i in range(remainder, 3):
                    spacer = QWidget()
                    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    grid.addWidget(spacer, len(formulas) // 3, i)

            scroll.setWidget(container)
            self._tabs.addTab(scroll, category)

        # 底部提示
        tip = QLabel("💡 点击公式即可插入文档。使用 $...$ 包裹行内公式，$$...$$ 包裹独立公式。")
        tip.setFont(QFont("PingFang SC", 9))
        tip.setStyleSheet("color: #999; padding: 4px 0;")
        layout.addWidget(tip)

    def _on_formula_clicked(self, latex: str):
        self._selected_latex = latex
        self.formula_selected.emit(latex)
        self.accept()

    def get_formula(self) -> str:
        return self._selected_latex

    def _filter(self, text: str):
        """Filter formula cards across all tabs based on search text."""
        keyword = text.strip().lower()
        for card, category, name in self._all_cards:
            visible = not keyword or keyword in name.lower() or keyword in category.lower()
            card.setVisible(visible)
