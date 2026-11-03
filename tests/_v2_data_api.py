"""Build v2 transport fixtures from historical v1 position fixtures."""
_KEYS = {'asset':'token_id','conditionId':'condition_id','size':'current_size',
         'avgPrice':'avg_price','currentValue':'current_value','curPrice':'current_price',
         'cashPnl':'unrealized_pnl','percentPnl':'percent_pnl','realizedPnl':'realized_pnl',
         'oppositeAsset':'opposite_token_id','negativeRisk':'negative_risk',
         'entryFeesUsdc':'entry_fees_usdc','totalBought':'total_size',
         'percentRealizedPnl':'percent_realized_pnl','outcomeIndex':'outcome_index',
         'eventId':'event_id','eventSlug':'event_slug','endDate':'end_date','proxyWallet':'proxy_wallet'}

def v1_row_to_v2(row):
    result = {_KEYS.get(k, k): v for k, v in row.items()}
    slug = row.get('slug', 'fixture')
    result.setdefault('token_id', slug + '-' + str(row.get('outcome', 'Yes')))
    result.setdefault('condition_id', 'cid-' + slug)
    size = row.get('size', 0)
    result.setdefault('avg_price', row.get('initialValue', 0) / float(size) if size and isinstance(size, (float,int)) else 0)
    result.setdefault('current_price', 0)
    result.setdefault('current_value', 0)
    return result

def envelope(rows):
    return {'data': [v1_row_to_v2(r) if isinstance(r, dict) else r for r in rows],
            'pagination': {'next_cursor': None}}
