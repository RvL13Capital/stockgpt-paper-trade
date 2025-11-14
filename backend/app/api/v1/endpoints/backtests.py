from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.core.database import get_db
from app.core.logging import logger
from app.models.backtest import Backtest, BacktestStatus, StrategyType, StrategyTemplate
from app.services.backtest_engine import backtest_engine
from app.services.reporting_service import reporting_service

router = APIRouter()

@router.post("/")
async def create_backtest(
    name: str,
    description: str,
    strategy_type: StrategyType,
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_capital: float = 100000.0,
    strategy_config: Optional[dict] = None,
    max_position_size: float = 0.1,
    stop_loss_pct: float = 0.05,
    take_profit_pct: float = 0.1,
    db: AsyncSession = Depends(get_db)
):
    """Create a new backtest"""
    
    try:
        backtest = Backtest(
            user_id=1,  # Mock user ID
            name=name,
            description=description,
            strategy_type=strategy_type,
            symbols=symbols,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            initial_capital=initial_capital,
            strategy_config=strategy_config,
            max_position_size=max_position_size,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
        )
        
        db.add(backtest)
        await db.commit()
        await db.refresh(backtest)
        
        logger.info(f"Created backtest: {backtest.name} ({backtest.id})")
        
        return {
            'message': 'Backtest created successfully',
            'backtest_id': backtest.id,
            'backtest': {
                'id': backtest.id,
                'name': backtest.name,
                'strategy_type': backtest.strategy_type.value,
                'symbols': backtest.symbols,
                'start_date': backtest.start_date.isoformat(),
                'end_date': backtest.end_date.isoformat(),
                'status': backtest.status.value,
                'created_at': backtest.created_at.isoformat(),
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backtest: {str(e)}")

@router.get("/")
async def get_backtests(
    status: Optional[BacktestStatus] = None,
    strategy_type: Optional[StrategyType] = None,
    limit: int = Query(default=50, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get list of backtests with filtering"""
    
    query = select(Backtest).order_by(desc(Backtest.created_at))
    
    if status:
        query = query.where(Backtest.status == status)
    
    if strategy_type:
        query = query.where(Backtest.strategy_type == strategy_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    backtests = result.scalars().all()
    
    return {
        'backtests': [
            {
                'id': bt.id,
                'name': bt.name,
                'strategy_type': bt.strategy_type.value,
                'symbols': bt.symbols,
                'start_date': bt.start_date.isoformat(),
                'end_date': bt.end_date.isoformat(),
                'status': bt.status.value,
                'total_return': bt.total_return,
                'sharpe_ratio': bt.sharpe_ratio,
                'max_drawdown': bt.max_drawdown,
                'win_rate': bt.win_rate,
                'total_trades': bt.total_trades,
                'created_at': bt.created_at.isoformat(),
                'completed_at': bt.completed_at.isoformat() if bt.completed_at else None,
            }
            for bt in backtests
        ],
        'total': len(backtests)
    }

@router.get("/{backtest_id}")
async def get_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed backtest information"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return {
        'id': backtest.id,
        'name': backtest.name,
        'description': backtest.description,
        'strategy_type': backtest.strategy_type.value,
        'strategy_config': backtest.strategy_config,
        'symbols': backtest.symbols,
        'start_date': backtest.start_date.isoformat(),
        'end_date': backtest.end_date.isoformat(),
        'initial_capital': backtest.initial_capital,
        'max_position_size': backtest.max_position_size,
        'stop_loss_pct': backtest.stop_loss_pct,
        'take_profit_pct': backtest.take_profit_pct,
        'status': backtest.status.value,
        'created_at': backtest.created_at.isoformat(),
        'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
        'completed_at': backtest.completed_at.isoformat() if backtest.completed_at else None,
        'error_message': backtest.error_message,
        # Performance metrics
        'total_return': backtest.total_return,
        'annualized_return': backtest.annualized_return,
        'volatility': backtest.volatility,
        'sharpe_ratio': backtest.sharpe_ratio,
        'max_drawdown': backtest.max_drawdown,
        'total_trades': backtest.total_trades,
        'winning_trades': backtest.winning_trades,
        'losing_trades': backtest.losing_trades,
        'win_rate': backtest.win_rate,
        'avg_win': backtest.avg_win,
        'avg_loss': backtest.avg_loss,
        'profit_factor': backtest.profit_factor,
        'var_95': backtest.var_95,
        'expected_shortfall': backtest.expected_shortfall,
        'calmar_ratio': backtest.calmar_ratio,
        'sortino_ratio': backtest.sortino_ratio,
        'avg_holding_period': backtest.avg_holding_period,
        'max_consecutive_wins': backtest.max_consecutive_wins,
        'max_consecutive_losses': backtest.max_consecutive_losses,
    }

@router.post("/{backtest_id}/run")
async def run_backtest(
    backtest_id: int,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Run a backtest"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    if backtest.status == BacktestStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Backtest already running")
    
    try:
        if background_tasks:
            # Run in background
            background_tasks.add_task(
                backtest_engine.run_backtest,
                db,
                backtest_id
            )
            
            return {
                'message': 'Backtest started in background',
                'backtest_id': backtest_id,
                'status': 'running'
            }
        else:
            # Run synchronously
            results = await backtest_engine.run_backtest(db, backtest_id)
            
            return {
                'message': 'Backtest completed successfully',
                'backtest_id': backtest_id,
                'status': 'completed',
                'results': results
            }
    
    except Exception as e:
        logger.error(f"Error running backtest {backtest_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")

@router.get("/{backtest_id}/results")
async def get_backtest_results(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get backtest results"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    if backtest.status != BacktestStatus.COMPLETED:
        return {'message': 'Backtest not completed yet', 'status': backtest.status.value}
    
    return {
        'backtest_id': backtest_id,
        'name': backtest.name,
        'strategy_type': backtest.strategy_type.value,
        'performance_metrics': {
            'total_return': backtest.total_return,
            'annualized_return': backtest.annualized_return,
            'volatility': backtest.volatility,
            'sharpe_ratio': backtest.sharpe_ratio,
            'max_drawdown': backtest.max_drawdown,
            'calmar_ratio': backtest.calmar_ratio,
            'total_trades': backtest.total_trades,
            'win_rate': backtest.win_rate,
            'profit_factor': backtest.profit_factor,
            'avg_holding_period': backtest.avg_holding_period,
        },
        'equity_curve': backtest.equity_curve,
        'monthly_returns': backtest.monthly_returns,
        'trades_history': backtest.trades_history,
    }

@router.post("/{backtest_id}/cancel")
async def cancel_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running backtest"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    if backtest.status != BacktestStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Backtest is not running")
    
    backtest.status = BacktestStatus.CANCELLED
    backtest.completed_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        'message': 'Backtest cancelled successfully',
        'backtest_id': backtest_id,
        'status': 'cancelled'
    }

@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a backtest"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    if backtest.status == BacktestStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot delete running backtest")
    
    await db.delete(backtest)
    await db.commit()
    
    return {
        'message': 'Backtest deleted successfully',
        'backtest_id': backtest_id
    }

@router.post("/compare")
async def compare_backtests(
    backtest_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple backtests"""
    
    try:
        comparison = await backtest_engine.compare_backtests(db, backtest_ids)
        return comparison
    
    except Exception as e:
        logger.error(f"Error comparing backtests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare backtests: {str(e)}")

# Strategy Templates
@router.get("/templates")
async def get_strategy_templates(
    strategy_type: Optional[StrategyType] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get strategy templates"""
    
    query = select(StrategyTemplate)
    
    if strategy_type:
        query = query.where(StrategyTemplate.strategy_type == strategy_type)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return {
        'templates': [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'strategy_type': t.strategy_type.value,
                'parameters': t.parameters,
                'entry_conditions': t.entry_conditions,
                'exit_conditions': t.exit_conditions,
                'default_stop_loss': t.default_stop_loss,
                'default_take_profit': t.default_take_profit,
                'default_position_size': t.default_position_size,
                'created_by': t.created_by,
                'created_at': t.created_at.isoformat(),
                'is_public': t.is_public,
                'usage_count': t.usage_count,
                'avg_performance': t.avg_performance,
            }
            for t in templates
        ]
    }

@router.post("/templates")
async def create_strategy_template(
    name: str,
    description: str,
    strategy_type: StrategyType,
    parameters: dict,
    entry_conditions: dict,
    exit_conditions: dict,
    default_stop_loss: float = 0.05,
    default_take_profit: float = 0.1,
    default_position_size: float = 0.1,
    is_public: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Create a strategy template"""
    
    template = StrategyTemplate(
        name=name,
        description=description,
        strategy_type=strategy_type,
        parameters=parameters,
        entry_conditions=entry_conditions,
        exit_conditions=exit_conditions,
        default_stop_loss=default_stop_loss,
        default_take_profit=default_take_profit,
        default_position_size=default_position_size,
        created_by='system',  # Mock user
        is_public=is_public,
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return {
        'message': 'Strategy template created successfully',
        'template_id': template.id
    }

# Reports
@router.get("/{backtest_id}/report")
async def get_backtest_report(
    backtest_id: int,
    format: str = Query(default='json', regex='^(json|csv|pdf)$'),
    db: AsyncSession = Depends(get_db)
):
    """Get backtest report in specified format"""
    
    backtest = await db.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    if backtest.status != BacktestStatus.COMPLETED:
        return {'message': 'Backtest not completed yet', 'status': backtest.status.value}
    
    # Generate report
    report = await reporting_service._generate_backtest_report(db, backtest_id)
    
    # Export in requested format
    exported_report = await reporting_service.export_report(report, format)
    
    return {
        'format': format,
        'content': exported_report,
        'filename': f"backtest_report_{backtest_id}.{format}"
    }