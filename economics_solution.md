# 경제학 문제 풀이

## 가. 예산제약식을 실질변수로 표현

### 주어진 명목 예산제약식들:
- **예산제약식 1**: $P_t c_t + M_t = (1+i_t)M_{t-1} + W_t n_t + T_t$
- **예산제약식 2**: $P_t c_t \leq M_{t-1} + T_t$
- **정부보조금**: $T_t = M_t - M_{t-1}$

### 풀이 과정:

**1단계: 예산제약식 1의 실질화**

명목 예산제약식 1을 $P_t$로 나누면:
$$\frac{P_t c_t}{P_t} + \frac{M_t}{P_t} = \frac{(1+i_t)M_{t-1}}{P_t} + \frac{W_t n_t}{P_t} + \frac{T_t}{P_t}$$

실질변수 정의를 사용하면:
$$c_t + m_t = \frac{(1+i_t)M_{t-1}}{P_t} + w_t n_t + \tau_t$$

여기서 $\frac{(1+i_t)M_{t-1}}{P_t} = \frac{(1+i_t)M_{t-1}}{P_{t-1}} \cdot \frac{P_{t-1}}{P_t}$

$\frac{P_{t-1}}{P_t} = \frac{1}{1+\pi_t}$ (∵ $\pi_t = \frac{P_t - P_{t-1}}{P_{t-1}}$)

따라서:
$$c_t + m_t = \frac{(1+i_t)}{(1+\pi_t)} m_{t-1} + w_t n_t + \tau_t$$

**2단계: 예산제약식 2의 실질화**

명목 예산제약식 2를 $P_t$로 나누면:
$$\frac{P_t c_t}{P_t} \leq \frac{M_{t-1}}{P_t} + \frac{T_t}{P_t}$$

$$c_t \leq \frac{M_{t-1}}{P_t} + \tau_t$$

$\frac{M_{t-1}}{P_t} = \frac{M_{t-1}}{P_{t-1}} \cdot \frac{P_{t-1}}{P_t} = \frac{m_{t-1}}{1+\pi_t}$

따라서:
$$c_t \leq \frac{m_{t-1}}{1+\pi_t} + \tau_t$$

### 결과:
- **예산제약식 1**: $c_t + m_t = \frac{1+i_t}{1+\pi_t} m_{t-1} + w_t n_t + \tau_t$
- **예산제약식 2**: $c_t \leq \frac{m_{t-1}}{1+\pi_t} + \tau_t$

## 나. 일계조건 도출 및 인플레이션의 노동공급 영향

### 라그랑지안 설정:

$$L = E_0 \sum_{t=0}^{\infty} \beta^t \left[ \ln c_t - \phi \frac{n_t^{1+\nu}}{1+\nu} + \lambda_t \left( \frac{1+i_t}{1+\pi_t} m_{t-1} + w_t n_t + \tau_t - c_t - m_t \right) + \mu_t \left( \frac{m_{t-1}}{1+\pi_t} + \tau_t - c_t \right) \right]$$

### 일계조건 도출:

**1. 소비 $c_t$에 대한 FOC:**
$$\frac{\partial L}{\partial c_t} = \beta^t \left[ \frac{1}{c_t} - \lambda_t - \mu_t \right] = 0$$

따라서: $\frac{1}{c_t} = \lambda_t + \mu_t$

**2. 화폐보유 $m_t$에 대한 FOC:**
$$\frac{\partial L}{\partial m_t} = \beta^t \left[ -\lambda_t + \beta E_t \lambda_{t+1} \frac{1+i_{t+1}}{1+\pi_{t+1}} + \beta E_t \mu_{t+1} \frac{1}{1+\pi_{t+1}} \right] = 0$$

따라서: $\lambda_t = \beta E_t \left[ \frac{\lambda_{t+1} + \mu_{t+1}}{1+\pi_{t+1}} \right] (1+i_{t+1})$

**3. 노동시간 $n_t$에 대한 FOC:**
$$\frac{\partial L}{\partial n_t} = \beta^t \left[ -\phi n_t^{\nu} + \lambda_t w_t \right] = 0$$

따라서: $\phi n_t^{\nu} = \lambda_t w_t$

### 균제상태 분석:

균제상태에서 모든 변수가 일정하므로 $E_t[\cdot] = (\cdot)$이고, 첨자 t를 생략할 수 있다.

**화폐보유 조건에서:**
$$\lambda = \beta \frac{(\lambda + \mu)}{1+\pi} (1+i)$$

**피셔방정식 사용:** $1+i = (1+r)(1+\pi)$이므로
$$\lambda = \beta (\lambda + \mu) (1+r)$$

**균제상태에서 $\beta(1+r) = 1$이므로:**
$$\lambda = \lambda + \mu$$
$$\mu = 0$$

이는 균제상태에서 현금보유제약(cash-in-advance constraint)이 binding하지 않음을 의미한다.

**노동공급 조건:**
$$\phi n^{\nu} = \lambda w = \frac{w}{c}$$

**인플레이션의 영향:**

균제상태에서 실질변수들은 인플레이션과 독립적이어야 하지만, 화폐보유 비용이 변화한다.

인플레이션이 상승하면:
1. **화폐보유 비용 증가**: 높은 인플레이션은 화폐보유의 기회비용을 증가시킨다
2. **인플레이션 세금 효과**: 정부가 화폐발행으로 얻는 seigniorage가 증가하지만, 가계의 실질 화폐보유량은 감소한다
3. **노동공급에 대한 간접효과**: 인플레이션이 실질임금이나 소비에 영향을 미치면 노동공급도 변화할 수 있다

### 인플레이션 세금과의 연관성:

**인플레이션 세tax**는 화폐보유자가 인플레이션으로 인해 겪는 실질 구매력 손실을 의미한다. 본 모형에서:

- 정부보조금 $T_t = M_t - M_{t-1}$는 seigniorage를 나타낸다
- 인플레이션이 높을수록 화폐보유의 기회비용이 증가하여 화폐수요가 감소한다
- 이는 결국 노동공급 결정에 영향을 미치는데, 실질소비와 실질임금의 상대적 변화를 통해 작용한다

**결론**: 균제상태에서 인플레이션 상승은 화폐보유 비용을 증가시켜 간접적으로 노동공급에 영향을 미치며, 이는 인플레이션 세금이 가계의 최적 선택에 왜곡을 가져오는 전형적인 사례이다.