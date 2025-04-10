from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.virtual_machine import VMInDB, VMCreate, VMUpdate, VirtualMachine
import logging

router = APIRouter(prefix="/vms", tags=["virtual-machines"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[VMInDB])
async def list_vms(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    os_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(VirtualMachine)
    
    if search:
        query = query.filter(
            VirtualMachine.name.ilike(f"%{search}%") |
            VirtualMachine.description.ilike(f"%{search}%")
        )
    
    if min_price is not None:
        query = query.filter(VirtualMachine.price >= min_price)
    
    if max_price is not None:
        query = query.filter(VirtualMachine.price <= max_price)
    
    if os_type:
        # Note: This assumes os_type is stored in specifications JSON
        query = query.filter(VirtualMachine.specifications['os_type'].astext == os_type)
    
    total = query.count()
    vms = query.offset(skip).limit(limit).all()
    
    return vms

@router.get("/{vm_id}", response_model=VMInDB)
async def get_vm(vm_id: int, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="Virtual machine not found")
    return vm

@router.post("/", response_model=VMInDB)
async def create_vm(
    vm: VMCreate,
    db: Session = Depends(get_db)
):
    db_vm = VirtualMachine(
        **vm.model_dump()
    )
    db.add(db_vm)
    db.commit()
    db.refresh(db_vm)
    return db_vm

@router.put("/{vm_id}", response_model=VMInDB)
async def update_vm(
    vm_id: int,
    vm_update: VMUpdate,
    db: Session = Depends(get_db)
):
    db_vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not db_vm:
        raise HTTPException(status_code=404, detail="Virtual machine not found")
    
    update_data = vm_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vm, field, value)
    
    db.commit()
    db.refresh(db_vm)
    return db_vm

@router.delete("/{vm_id}")
async def delete_vm(
    vm_id: int,
    db: Session = Depends(get_db)
):
    db_vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not db_vm:
        raise HTTPException(status_code=404, detail="Virtual machine not found")
    
    db.delete(db_vm)
    db.commit()
    return {"message": "Virtual machine deleted successfully"} 